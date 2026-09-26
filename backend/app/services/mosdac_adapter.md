# MOSDAC Integration Plan

MOSDAC provides satellite-data access through its data-download API. Its
official documentation states that dataset search can be performed without
login, while downloads require MOSDAC credentials and a datasetId.

ORCA should treat MOSDAC as an optional satellite-data provider rather than
making it a hard runtime dependency.

Recommended future normalized fields:

- dataset_id
- acquisition_time
- bounding_box
- product_url or local artifact
- satellite
- sensor
- source/provider

Official reference:

https://www.mosdac.gov.in/downloadapi-manual
