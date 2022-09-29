catalog.uid = <dtml-var table_0>.uid

-- follow up
AND <dtml-var table_0>.base_category_uid = <dtml-var "portal_categories.follow_up.getUid()">
AND ((<dtml-var table_1>.parent_uid = <dtml-var table_0>.category_uid AND <dtml-var table_2>.uid = <dtml-var table_1>.uid)
  OR <dtml-var table_1>.uid = <dtml-var table_0>.category_uid AND <dtml-var table_2>.uid = <dtml-var table_1>.uid)

-- aggregate
AND <dtml-var table_2>.base_category_uid = <dtml-var "portal_categories.aggregate.getUid()">
AND <dtml-var table_2>.category_uid = <dtml-var table_3>.uid

