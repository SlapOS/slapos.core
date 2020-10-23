DELETE FROM
  roles_and_users
WHERE
  uid = <dtml-sqlvar expr="security_uid" type="string">
