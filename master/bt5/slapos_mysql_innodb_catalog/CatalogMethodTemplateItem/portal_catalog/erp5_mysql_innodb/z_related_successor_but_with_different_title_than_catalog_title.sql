<dtml-var table_1>.uid = <dtml-var table_0>.category_uid
AND <dtml-var table_0>.base_category_uid = <dtml-var "portal_categories.successor.getUid()">
<dtml-var RELATED_QUERY_SEPARATOR>
<dtml-var table_1>.title <> <dtml-var query_table>.title
AND <dtml-var table_0>.uid = <dtml-var query_table>.uid