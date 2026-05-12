Prediction Serving
==================

This section documents how recommendation results are served by the batch-based backend.

Serving Model
-------------

The backend does not compute recommendations during request handling.

Instead, recommendations are generated offline and stored in a prediction artifact.

The serving flow is:

::

   Offline generation -> predictions.parquet -> S3 -> Lambda startup load -> lookup -> response

Prediction Artifact
-------------------

The central serving artifact is:

- ``predictions.parquet``

This file contains precomputed recommendation results and is stored in Amazon S3.

Runtime Loading
---------------

At startup, the backend:

1. reads S3 configuration from environment variables
2. downloads ``predictions.parquet``
3. loads the file into memory
4. builds an internal lookup structure

Conceptually, the lookup behaves like:

::

   (anchor_id, kiosk_id) -> list of product_ids

Once initialized, requests are answered through lookup only.

Operational Consequence
-----------------------

Serving depends on two separate layers:

- backend image
- prediction artifact

This means code deployment and prediction refresh are independent processes.

A new image does not automatically imply new predictions, and a new prediction file does not require code changes as long as the format stays compatible.

Current State
-------------

In the current setup:

- backend deployment is automated through CI/CD
- the prediction artifact is stored in S3
- artifact refresh is handled separately from deployment

Summary
-------

The batch-based backend serves recommendations from a precomputed S3-hosted artifact loaded into memory during startup.