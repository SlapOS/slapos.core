select 
    catalog.uid,
    catalog.relative_url,
    catalog.portal_type
from 
    catalog 
left outer join 
    jio_api_revision on catalog.uid = jio_api_revision.uid
join 
    slapos_item on catalog.uid = slapos_item.uid
where 
    (jio_api_revision.uid IS NULL
    OR jio_api_revision.web_section!=<dtml-sqlvar expr="web_section" type="string" optional>)
    AND (catalog.portal_type="Slave Instance" OR catalog.portal_type="Software Instance")
    AND slapos_item.slap_state!="draft"
    AND catalog.validation_state="validated"

