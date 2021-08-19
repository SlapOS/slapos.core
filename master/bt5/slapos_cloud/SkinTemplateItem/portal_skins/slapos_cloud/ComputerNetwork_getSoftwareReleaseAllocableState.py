network = context

# XXX - The use of current authenticated person will return always 'Close' if
#       the person is administrator (such as 'zope' user) but not the owner of compute_node
#
#       person = portal.portal_membership.getAuthenticatedMember().getUserValue()

allocation_state = 'Close'
software_type = ''
filter_kw = {}

for compute_node in network.getSubordinationRelatedValueList():
  person = compute_node.getSourceAdministrationValue()
  filter_kw['compute_node_guid']=compute_node.getReference()
  try:
    isAllowed =  person.Person_restrictMethodAsShadowUser(shadow_document=person,
          callable_object=person.Person_findPartition,
          argument_list=[software_release_url, software_type, 'Software Instance',
                         filter_kw],
          argument_dict={'test_mode': True}
    )
    if isAllowed:
      allocation_state = 'Open'
      break
  except Exception:
    continue

return allocation_state
