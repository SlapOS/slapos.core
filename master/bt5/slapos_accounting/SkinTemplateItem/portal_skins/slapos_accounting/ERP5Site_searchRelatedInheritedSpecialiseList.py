portal = context
result_list = []

if specialise_uid is None:
  current_uid_list = []
elif same_type(specialise_uid, []) or same_type(specialise_uid, ()):
  current_uid_list = list(specialise_uid)
else:
  current_uid_list = [specialise_uid]

search_kw = {}
if portal_type is not None:
  search_kw['portal_type'] = portal_type
if validation_state is not None:
  search_kw['validation_state'] = validation_state
if destination_section__uid is not None:
  search_kw['destination_section__uid'] = destination_section__uid

# This is REALLY INEFFICIENT.
# Keep it simple for now, as the goal is probably to drop all this script usage
while (current_uid_list):
  specialise__uid = current_uid_list
  current_uid_list = []
  for sql_result in portal.portal_catalog(
    specialise__uid=specialise__uid,
    **search_kw
  ):
    current_uid_list.append(sql_result.uid)
    result_list.append(sql_result)

return result_list
