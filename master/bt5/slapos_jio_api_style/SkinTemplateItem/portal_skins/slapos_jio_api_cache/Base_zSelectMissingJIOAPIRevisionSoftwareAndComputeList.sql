select 
    catalog.uid,
    catalog.relative_url,
    catalog.portal_type
from 
    catalog 
left outer join 
    jio_api_revision on catalog.uid = jio_api_revision.uid
where 
    (jio_api_revision.uid IS NULL
    OR jio_api_revision.web_section!=<dtml-sqlvar expr="web_section" type="string">)
    AND (catalog.portal_type="Compute Node" OR catalog.portal_type="Software Installation")
    AND catalog.validation_state="validated"
