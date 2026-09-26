# INCOIS PFZ Adapter Plan

ORCA currently uses demo PFZ data for the Ocean Agent.

The production integration point is backend/app/services/ocean_service.py.

INCOIS publishes Potential Fishing Zone advisory information through its
WebGIS and maintains PFZ advisory data holdings. The ORCA adapter should use
an approved INCOIS access mechanism and normalize it to:

- location
- PFZ latitude/longitude
- direction
- distance
- advisory timestamp
- source/provider
- data mode

Do not scrape or invent an undocumented API endpoint.

Official references:

- https://www.incois.gov.in/MarineFisheries/PfzWebGis
- https://incois.gov.in/site/dataholdings.jsp

Until an approved machine-readable feed is configured, ORCA keeps the demo
fallback and labels it as demo.
