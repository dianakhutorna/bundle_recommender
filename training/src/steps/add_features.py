"""
Compute all features for the bundle recommendation LightGBM model.

Input:  base feature table with (kiosk_id, anchor_product_id, candidate_product_id, cooc_cosine_sim)
Output: same table enriched with features ready for LightGBM.

Features added:
  pop_store          — how many times this kiosk ordered the candidate product
  pop_global         — how many times the candidate was ordered across all kiosks
  kiosk_product_cnt  — total order rows for this kiosk (proxy for kiosk size)
  same_category      — 1 if anchor and candidate share the same product category
  cand_is_new        — 1 if the kiosk has never ordered the candidate before
  channel            — kiosk sales channel  (categorical, kept as string)
  region             — kiosk geographic region (categorical, kept as string)

Seasonality features (when enabled):
  query_month_sin    — sin(2π·month/12)   cyclical month encoding of query time
  query_month_cos    — cos(2π·month/12)   cyclical month encoding of query time
  cand_seasonal_pop  — candidate popularity in query month vs average month
  cand_recency_days  — days since the kiosk last ordered this candidate (capped at 365)
"""

from __future__ import annotations

import math

import polars as pl

KEY_COLS = ["kiosk_id", "anchor_product_id", "candidate_product_id"]


def add_features(
    feature_table: pl.DataFrame,
    *,
    orders: pl.DataFrame,
    products: pl.DataFrame | None = None,
    commerces: pl.DataFrame | None = None,
    include_seasonality: bool = False,
) -> pl.DataFrame:
    """Add all features to the base feature table in a single pass."""
    ft = feature_table

    # ---- popularity: store-level (kiosk × candidate) ----
    kiosk_product_counts = (
        orders
        .group_by(["kiosk_id", "product_id"])
        .len()
        .rename({"len": "pop_store"})
    )
    ft = ft.join(
        kiosk_product_counts,
        left_on=["kiosk_id", "candidate_product_id"],
        right_on=["kiosk_id", "product_id"],
        how="left",
    ).with_columns(pl.col("pop_store").fill_null(0))

    # ---- popularity: global (candidate across all kiosks) ----
    pop_global = (
        kiosk_product_counts
        .group_by("product_id")
        .agg(pl.col("pop_store").sum().alias("pop_global"))
    )
    ft = ft.join(
        pop_global,
        left_on="candidate_product_id",
        right_on="product_id",
        how="left",
    ).with_columns(pl.col("pop_global").fill_null(0))

    # ---- kiosk volume ----
    kiosk_stats = (
        orders
        .group_by("kiosk_id")
        .agg(pl.len().alias("kiosk_product_cnt"))
    )
    ft = ft.join(kiosk_stats, on="kiosk_id", how="left").with_columns(
        pl.col("kiosk_product_cnt").fill_null(0)
    )

    # ---- is-new: kiosk never ordered this candidate ----
    ft = ft.with_columns(
        (pl.col("pop_store") == 0).cast(pl.Int8).alias("cand_is_new")
    )

    # ---- product category pair feature ----
    if products is not None and "productid" in products.columns and "category" in products.columns:
        prod = (
            products
            .select(
                pl.col("productid").alias("product_id"),
                pl.col("category"),
            )
            .unique(subset=["product_id"])
        )
        ft = (
            ft
            .join(
                prod.rename({"product_id": "anchor_product_id", "category": "anchor_cat"}),
                on="anchor_product_id",
                how="left",
            )
            .join(
                prod.rename({"product_id": "candidate_product_id", "category": "cand_cat"}),
                on="candidate_product_id",
                how="left",
            )
            .with_columns(
                (pl.col("anchor_cat") == pl.col("cand_cat")).cast(pl.Int8).alias("same_category")
            )
            .drop(["anchor_cat", "cand_cat"])
        )

    # ---- kiosk metadata (channel, region) ----
    if commerces is not None and "userid" in commerces.columns:
        comm = commerces.select(
            pl.col("userid").alias("kiosk_id"),
            "channel",
            "region",
        )
        ft = ft.join(comm, on="kiosk_id", how="left")

    # ---- seasonality features ----
    if include_seasonality:
        ft = _add_seasonality_features(ft, orders=orders)

    return ft


# ============================================================
# Seasonality helpers
# ============================================================

def _add_seasonality_features(
    ft: pl.DataFrame,
    *,
    orders: pl.DataFrame,
) -> pl.DataFrame:
    """
    Add time-aware features that capture seasonal purchase patterns.

    Features:
      query_month_sin / query_month_cos — cyclical encoding of the kiosk's
          latest order month (a proxy for "query time").
      cand_seasonal_pop — ratio of candidate orders in the query month
          versus its average monthly orders. >1 means the product is popular
          *in that month*.
      cand_recency_days — days since the kiosk last ordered this candidate.
          Capped at 365; set to 365 if never ordered.
    """

    # 1) Determine "query month" for each kiosk — use the latest order date.
    kiosk_latest = (
        orders
        .group_by("kiosk_id")
        .agg(pl.col("order_dt").max().alias("latest_order_dt"))
        .with_columns(
            pl.col("latest_order_dt").dt.month().alias("query_month"),
        )
    )

    ft = ft.join(
        kiosk_latest.select("kiosk_id", "query_month", "latest_order_dt"),
        on="kiosk_id",
        how="left",
    )

    # 2) Cyclical month encoding (sin/cos)
    ft = ft.with_columns(
        (2.0 * math.pi * pl.col("query_month").cast(pl.Float64) / 12.0)
        .sin()
        .alias("query_month_sin"),
        (2.0 * math.pi * pl.col("query_month").cast(pl.Float64) / 12.0)
        .cos()
        .alias("query_month_cos"),
    )

    # 3) Candidate seasonal popularity — orders in month / avg monthly orders
    product_monthly = (
        orders
        .with_columns(pl.col("order_dt").dt.month().alias("month"))
        .group_by(["product_id", "month"])
        .len()
        .rename({"len": "month_orders"})
    )
    product_avg = (
        product_monthly
        .group_by("product_id")
        .agg(pl.col("month_orders").mean().alias("avg_monthly_orders"))
    )
    product_seasonal = product_monthly.join(product_avg, on="product_id", how="left").with_columns(
        (pl.col("month_orders") / pl.col("avg_monthly_orders"))
        .fill_null(1.0)
        .alias("cand_seasonal_pop"),
    ).select("product_id", "month", "cand_seasonal_pop")

    ft = ft.join(
        product_seasonal,
        left_on=["candidate_product_id", "query_month"],
        right_on=["product_id", "month"],
        how="left",
    ).with_columns(pl.col("cand_seasonal_pop").fill_null(1.0))

    # 4) Recency — days since the kiosk last ordered this candidate
    kiosk_product_last = (
        orders
        .group_by(["kiosk_id", "product_id"])
        .agg(pl.col("order_dt").max().alias("last_cand_order_dt"))
    )
    ft = ft.join(
        kiosk_product_last,
        left_on=["kiosk_id", "candidate_product_id"],
        right_on=["kiosk_id", "product_id"],
        how="left",
    )
    ft = ft.with_columns(
        (
            (pl.col("latest_order_dt") - pl.col("last_cand_order_dt"))
            .dt.total_days()
            .fill_null(365)
            .clip(0, 365)
            .cast(pl.Float64)
        ).alias("cand_recency_days"),
    )

    # Drop intermediate columns
    ft = ft.drop(["query_month", "latest_order_dt", "last_cand_order_dt"], strict=False)

    return ft
