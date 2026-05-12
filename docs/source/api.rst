API
===

This section documents the external API of the batch-based bundle recommender backend.

Overview
--------

The backend exposes a small HTTP API for serving recommendation results.

The API structure is intentionally aligned with the other backend variant.

Endpoints
---------

The backend exposes the following endpoints:

- ``GET /health``
- ``GET /recommendations``
- ``POST /recommendations/multi``

Base URL
--------

The exact base URL depends on the deployed API Gateway configuration.

Example deployment used during the project:

::

   https://0pwj7mrtz4.execute-api.eu-central-1.amazonaws.com

GET /health
-----------

Used to verify service availability.

Example request:

.. code-block:: bash

   curl "https://.../health"

Typical response:

.. code-block:: json

   {"status":"ok"}

GET /recommendations
--------------------

Used for a single recommendation request.

Query parameters:

- ``anchorId``
- ``kioskId``
- ``limit``

Example request:

.. code-block:: bash

   curl "https://.../recommendations?anchorId=000600-001&kioskId=ab748276f5cdca69ee0c03002fedb5dd&limit=5"

Typical response structure:

.. code-block:: json

   [
     {
       "anchor_id": "000600-001",
       "kiosk_id": "ab748276f5cdca69ee0c03002fedb5dd",
       "product_id": "000120-001",
       "model_id": "diana_model_v1",
       "recommendation_date": "2026-03-26T17:45:37.410410Z"
     }
   ]

POST /recommendations/multi
---------------------------

Used to request multiple recommendation sets in one call.

Request body fields:

- ``anchor_id``
- ``kiosk_id``

Example request:

.. code-block:: bash

   curl -X POST "https://.../recommendations/multi" \
     -H "Content-Type: application/json" \
     -d '[
       {
         "anchor_id": "000600-001",
         "kiosk_id": "ab748276f5cdca69ee0c03002fedb5dd"
       }
     ]'

Typical response structure:

.. code-block:: json

   [
     {
       "anchor_id": "000600-001",
       "kiosk_id": "ab748276f5cdca69ee0c03002fedb5dd",
       "recs": [
         "000120-001",
         "000617-001",
         "000300-002"
       ],
       "model_id": "diana_model_v1",
       "recommendation_date": "2026-03-26T17:45:47.401420Z"
     }
   ]

API Design Note
---------------

The API contract matches the other backend variant on purpose.

This makes it possible to:

- integrate both backends in the same way
- compare them in parallel
- support A/B testing scenarios without changing the client interface

