Deployment
==========

This section documents the deployment setup of the batch-based bundle recommender backend.

Overview
--------

The backend is deployed as a containerized FastAPI service on AWS Lambda.

Deployment flow:

::

   GitHub -> GitHub Actions -> Docker -> Amazon ECR -> AWS Lambda -> API Gateway

In addition to code deployment, this backend also depends on a prediction artifact stored in Amazon S3.

Deployment Scope
----------------

The deployment setup covers:

- backend code
- container image build
- image storage in ECR
- Lambda deployment
- API exposure through API Gateway

The prediction artifact lifecycle is separate from the code deployment lifecycle.

Runtime Model
-------------

This backend does not compute recommendations during request processing.

Instead, it:

- loads a precomputed prediction file during startup
- builds an in-memory lookup
- serves recommendation results via lookup

At a high level:

::

   Offline prediction generation -> predictions.parquet -> S3 -> Lambda startup load -> API response

Main AWS Components
-------------------

The deployed backend uses:

- Amazon ECR for image storage
- AWS Lambda for execution
- Amazon API Gateway for public access
- Amazon S3 for prediction artifact storage
- IAM for runtime and deployment permissions
- CloudWatch Logs for monitoring

Containerization
----------------

The backend is packaged as a Lambda-compatible Docker image.

Typical Dockerfile:

.. code-block:: dockerfile

   FROM public.ecr.aws/lambda/python:3.12

   COPY requirements-backend.txt .
   RUN pip install --no-cache-dir -r requirements-backend.txt

   COPY training /var/task/training

   CMD ["training.src.scripts.lambda_handler.handler"]

The image contains the backend code and runtime dependencies, but not the prediction artifact itself.

Prediction Artifact
-------------------

The backend depends on the file:

- ``predictions.parquet``

This file is stored separately in Amazon S3 and loaded at runtime.

This design keeps the image smaller and allows prediction data to be updated independently from backend code.

Deployment Validation
---------------------

After deployment, the following checks are recommended:

1. confirm that the GitHub Actions workflow completed successfully
2. verify that Lambda references the updated image
3. call ``/health``
4. test a known recommendation request
5. verify that the prediction file is still available in S3


