DELETE FROM roles_and_users
<dtml-var sql_delimiter>
INSERT INTO roles_and_users (uid, local_roles_group_id, allowedRolesAndUsers) VALUES
<dtml-in prefix="role" expr="getPortalObject().ERP5Site_getSecurityUidListForRecreateTable()">
(<dtml-sqlvar expr="role_item[2]" type="int">, <dtml-sqlvar expr="role_item[0]" type="string">, <dtml-sqlvar expr="role_item[1]" type="string">)<dtml-if sequence-end><dtml-else>,
</dtml-if>
</dtml-in>