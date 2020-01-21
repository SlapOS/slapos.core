SELECT
  catalog.uid, catalog.path
FROM
  catalog, catalog as open_sale_order_line_catalog
WHERE
  1=1
  AND catalog.path != 'reserved'
  AND open_sale_order_line_catalog.path != 'reserved'
  AND catalog.portal_type = "Open Sale Order"
  AND catalog.uid = open_sale_order_line_catalog.parent_uid
  AND catalog.validation_state IN ('draft', 'validated', 'archived')
  AND open_sale_order_line_catalog.portal_type = "Open Sale Order Line"
  AND open_sale_order_line_catalog.indexation_timestamp > catalog.indexation_timestamp
group by
  catalog.uid
