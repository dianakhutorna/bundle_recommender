AWS Configuration
=================

This section documents the AWS resources and settings required to run the batch-based bundle recommender backend.

Region
------

The backend is deployed in:

- ``eu-central-1``

Core AWS Resources
------------------

The backend depends on:

- Amazon ECR
- AWS Lambda
- Amazon API Gateway
- Amazon S3
- IAM
- Amazon CloudWatch Logs

Amazon ECR
----------

Amazon ECR stores the backend container image.

Example repository:

- ``diana-backend``

AWS Lambda
----------

AWS Lambda runs the backend service.

Example function:

- ``diana-backend``

Relevant Lambda settings include:

- image-based deployment
- execution role
- memory configuration
- timeout configuration
- environment variables

Amazon API Gateway
------------------

Amazon API Gateway exposes the backend as a public HTTP service.

Example endpoint:

::

   https://0pwj7mrtz4.execute-api.eu-central-1.amazonaws.com

Amazon S3
---------

Amazon S3 stores the prediction artifact required for serving.

Example bucket and key used during the project:

- bucket: ``yom-diana-backend-artifacts-124661688886-eu-central-1-an``
- key: ``diana/predictions/predictions.parquet``

IAM
---

IAM is used for:

- Lambda execution permissions
- deployment permissions for GitHub Actions

Lambda execution role
~~~~~~~~~~~~~~~~~~~~~

The Lambda execution role must allow:

- writing logs to CloudWatch
- reading the prediction artifact from S3

At minimum, this usually includes:

- ``s3:GetObject`` on the prediction file
- ``s3:ListBucket`` where required by the access pattern

Deployment role
~~~~~~~~~~~~~~~

The deployment role is used by GitHub Actions.

It must allow:

- authentication via OIDC
- pushing images to ECR
- updating the Lambda function

CloudWatch Logs
---------------

CloudWatch Logs is used for:

- startup diagnostics
- runtime debugging
- identifying import and S3 access errors

Environment Variables
---------------------

The batch-based backend uses the following runtime variables:

- ``PREDICTIONS_S3_BUCKET``
- ``PREDICTIONS_S3_KEY``
- ``MODEL_ID``

Example values:

.. code-block:: text

   PREDICTIONS_S3_BUCKET=yom-diana-backend-artifacts-124661688886-eu-central-1-an
   PREDICTIONS_S3_KEY=diana/predictions/predictions.parquet
   MODEL_ID=diana_model_v1

Configuration Checks
--------------------

The following points should be verified during setup and handover:

- correct AWS region
- existing ECR repository
- correct Lambda function
- valid API Gateway integration
- existing S3 bucket and object key
- attached Lambda execution role
- correct environment variables
- working CloudWatch logging

