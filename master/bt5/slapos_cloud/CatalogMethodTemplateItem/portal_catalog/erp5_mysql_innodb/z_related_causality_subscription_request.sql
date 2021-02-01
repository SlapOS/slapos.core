<dtml-var table_0>.base_category_uid = <dtml-var "portal_categories.causality.getUid()">
AND <dtml-var table_1>.uid = <dtml-var table_0>.uid
AND <dtml-var table_1>.portal_type = 'Subscription Request'
AND <dtml-var table_1>.simulation_state != 'deleted'

<dtml-var RELATED_QUERY_SEPARATOR>
<dtml-var table_0>.category_uid = <dtml-var query_table>.uid

