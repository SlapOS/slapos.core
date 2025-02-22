castToStr = context.Base_castDictToXMLString

portal = context.getPortalObject()

# Loads partition parameter
partition_parameter = data_dict.get("parameters", {})
# filter dict
filter_kw = data_dict.get("sla_parameters", {})

partition_reference = data_dict.get("title")
kw = dict(software_release=data_dict.get("software_release_uri"),
          software_type=data_dict.get("software_type"),
          software_title=partition_reference,
          instance_xml=castToStr(partition_parameter),
          shared=data_dict.get("shared", False),
          sla_xml=castToStr(filter_kw),
          state=data_dict.get("state", "started"),
          project_reference=data_dict.get("project_reference", None))


requester = portal.portal_membership.getAuthenticatedMember().getUserValue()
if requester.getPortalType() == 'Software Instance':
  instance_tree = requester.getSpecialiseValue()
  kw["project_reference"] = instance_tree.getFollowUpReference()
  # Speed up stop of all instances
  if instance_tree.getSlapState() == "stop_requested":
    kw['state'] = 'stopped'
  key = '_'.join([instance_tree.getRelativeUrl(), partition_reference])
else:
  # requested as root, so done by human
  requester = portal.portal_membership.getAuthenticatedMember().getUserValue()
  key = '_'.join([requester.getRelativeUrl(), partition_reference])

last_data = requester.getLastData(key)
requested_software_instance = None
value = dict(
  hash='_'.join([requester.getRelativeUrl(), str(kw)]),
  )

if last_data is not None and isinstance(last_data, type(value)):
  requested_software_instance = portal.restrictedTraverse(
      last_data.get('request_instance'), None)

if last_data is None or not isinstance(last_data, type(value)) or \
  last_data.get('hash') != value['hash'] or \
  requested_software_instance is None:
  if requester.getPortalType() == 'Software Instance':
    requester.requestInstance(**kw)
  else:
    # requester is a person so we use another method
    requester.requestSoftwareInstance(**kw)
  requested_software_instance = context.REQUEST.get('request_instance')
  if requested_software_instance is not None:
    value['request_instance'] = requested_software_instance\
      .getRelativeUrl()
    requester.setLastData(value, key=key)

if requested_software_instance is not None:
  return requested_software_instance.asJSONText()

return {
  'message': 'Software Instance Not Ready',
  'status': 102,
  'name': 'SoftwareInstanceNotReady'
}
