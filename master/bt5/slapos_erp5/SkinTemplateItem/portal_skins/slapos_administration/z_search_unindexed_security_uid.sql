select
  distinct catalog.<dtml-var security_uid_column> as security_uid, path, portal_type, uid

from
  catalog

where
  portal_type != "Business Template"
  and path not like "deleted"
  and catalog.<dtml-var security_uid_column> is not NULL
  and not exists (
     select
       roles_and_users.uid
     from
       roles_and_users
    where
       catalog.<dtml-var security_uid_column> = roles_and_users.uid
    )