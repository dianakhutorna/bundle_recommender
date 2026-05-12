Backend Architecture
====================

This section describes the backend architecture of the batch-based bundle recommender service.

Overview
--------

The backend is designed as a lookup-based API service.

Main components:

- FastAPI application layer
- AWS Lambda runtime
- Amazon API Gateway as public entry point
- Amazon S3 for prediction artifact storage
- in-memory lookup for serving recommendations

High-level flow:

::

   Client -> API Gateway -> Lambda -> FastAPI -> lookup -> response

Serving Principle
-----------------

The backend follows a batch-based serving approach.

Recommendations are generated offline in advance and stored as a prediction artifact.

At runtime, the backend only:

- loads the artifact
- builds the lookup structure
- returns precomputed results

This keeps the request path lightweight.

Application Layer
-----------------

FastAPI is used for:

- defining endpoints
- validating requests
- calling the serving layer
- formatting responses

The application does not perform heavy recommendation computation during the request.

Runtime Initialization
----------------------

During startup, the backend performs the following steps:

1. read S3 configuration from environment variables
2. download ``predictions.parquet`` from S3
3. load the file into memory
4. build a lookup structure

Conceptually, the lookup behaves like:

::

   (anchor_id, kiosk_id) -> list of product_ids

Request Handling
----------------

Once startup is complete, request handling is simple:

::

   Request -> lookup -> response

This reduces runtime complexity compared to live recommendation computation.

Runtime Dependencies
--------------------

The backend depends on:

- deployed container image
- valid Lambda configuration
- accessible S3 prediction artifact
- correct environment variables

If any of these components is missing or misconfigured, the backend may fail during startup.

Comparison to On-the-Fly Serving
--------------------------------

This backend differs from an on-the-fly system in one main architectural aspect:

- recommendation generation happens offline
- serving happens online through lookup

The runtime therefore depends on both backend code and prediction artifact state.

Summary
-------

The batch-based backend is built around a simple serving layer backed by an S3-hosted prediction file and an in-memory lookup initialized during Lambda startup.