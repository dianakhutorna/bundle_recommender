Troubleshooting
===============

This section lists common issues that may occur when deploying or running the batch-based bundle recommender backend.

Recommended Debugging Order
---------------------------

Use this order when a problem occurs:

1. test whether the API is reachable
2. call ``/health``
3. inspect CloudWatch logs
4. verify Lambda configuration
5. verify S3 artifact availability
6. inspect the GitHub Actions run if deployment was recent

API Returns Internal Server Error
---------------------------------

Symptom
~~~~~~~

.. code-block:: json

   {"message":"Internal Server Error"}

Likely causes
~~~~~~~~~~~~~

- Lambda startup failure
- missing environment variable
- S3 access failure
- missing or invalid prediction artifact
- runtime import error

Checks
~~~~~~

- test ``/health``
- inspect CloudWatch logs
- verify Lambda configuration
- verify S3 bucket and key settings

Health Endpoint Fails
---------------------

Symptom
~~~~~~~

``/health`` also fails.

Likely causes
~~~~~~~~~~~~~

- backend did not complete startup
- prediction file could not be loaded
- missing Python module
- invalid runtime configuration

Checks
~~~~~~

- inspect CloudWatch logs
- check for import errors
- check for S3-related exceptions
- verify environment variables

S3 Access Fails
---------------

Symptom
~~~~~~~

Startup fails with S3-related errors such as:

- ``403 Forbidden``
- ``404 Not Found``
- ``HeadObject operation: Forbidden``
- ``HeadObject operation: Not Found``

Likely causes
~~~~~~~~~~~~~

- wrong bucket name
- wrong object key
- missing S3 permissions
- missing prediction file

Checks
~~~~~~

- verify ``PREDICTIONS_S3_BUCKET``
- verify ``PREDICTIONS_S3_KEY``
- verify the object exists in S3
- verify Lambda execution role permissions

Interpretation
~~~~~~~~~~~~~~

- ``404`` usually means wrong path or missing object
- ``403`` usually means missing permissions

Runtime Import Errors
---------------------

Symptom
~~~~~~~

CloudWatch shows:

.. code-block:: text

   Runtime.ImportModuleError: Unable to import module ...

Likely causes
~~~~~~~~~~~~~

- required files missing from the image
- source files not committed
- wrong Dockerfile copy path
- package structure mismatch

Checks
~~~~~~

- verify repository contents
- verify committed files
- inspect Dockerfile ``COPY`` instructions
- verify the Lambda handler path

GitHub Actions Cannot Assume AWS Role
-------------------------------------

Symptom
~~~~~~~

GitHub Actions fails with:

.. code-block:: text

   Not authorized to perform sts:AssumeRoleWithWebIdentity

Likely causes
~~~~~~~~~~~~~

- incorrect ``AWS_ROLE_ARN`` secret
- invalid OIDC trust relationship
- repository or branch not allowed in IAM trust policy

Checks
~~~~~~

- verify ``AWS_ROLE_ARN``
- inspect IAM trust relationship
- confirm allowed repository and branch

Deployment Succeeds but Predictions Are Wrong or Outdated
---------------------------------------------------------

Likely causes
~~~~~~~~~~~~~

- new backend image was deployed, but the old prediction file is still in S3
- a new prediction file was expected but not uploaded
- backend is still using an older in-memory state after startup

Checks
~~~~~~

- verify the current S3 object
- confirm that the intended file was uploaded
- restart or redeploy the backend if a reload is needed

Lambda Rejects the Image
------------------------

Symptom
~~~~~~~

Lambda rejects the container image.

Likely causes
~~~~~~~~~~~~~

- wrong build architecture
- incompatible image manifest
- unsupported build metadata

Checks
~~~~~~

- build for ``linux/amd64``
- use Docker Buildx
- disable provenance metadata if needed

Summary
-------

Most issues in this backend setup are caused by one of the following:

- S3 artifact problems
- missing permissions
- deployment/runtime mismatch
- missing source files
- Lambda startup failures

In most cases, the fastest diagnosis path is:

- test ``/health``
- inspect CloudWatch logs
- verify S3 configuration and artifact availability