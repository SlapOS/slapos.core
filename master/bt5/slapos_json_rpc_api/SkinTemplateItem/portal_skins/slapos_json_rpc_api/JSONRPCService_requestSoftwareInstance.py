castToStr = context.Base_castDictToXMLString

portal = context.getPortalObject()

software_release = data_dict.get("software_release_uri")
software_type = data_dict.get("software_type")
# Loads partition parameter
partition_parameter = data_dict.get("parameters", {})
# filter dict
filter_kw = data_dict.get("sla_parameters", {})

# Keep compatibility with SlapTool behaviour
# XXX move retention delay to the resiliency stack
if (software_type == 'pull-backup') and (not 'retention_delay' in filter_kw):
  filter_kw['retention_delay'] = 7.0

partition_reference = data_dict.get("title")
kw = dict(software_release=software_release,
          software_type=software_type,
          software_title=partition_reference,
          instance_xml=castToStr(partition_parameter),
          shared=data_dict.get("shared", False),
          sla_xml=castToStr(filter_kw),
          state=data_dict.get("state", "started"))


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

  # Compatibility with the slapos console client
  # which does not send any project_reference parameter
  # and always connect to a uniq url
  # Try to guess the project reference automatically
  project_list = portal.portal_catalog(portal_type='Project', limit=2)
  if len(project_list) == 1:
    # If the user only has access to one project
    # we can easily suppose the request must be allocated here
    kw['project_reference'] = project_list[0].getReference()
  else:
    release_variation_list = portal.portal_catalog(
      portal_type='Software Product Release Variation',
      url_string=software_release,
      limit=2
    )
    if len(release_variation_list) == 1:
      # If the user only has access to matching release variation
      # we can easily suppose the request must be allocated on the same project
      kw['project_reference'] = release_variation_list[0].getParentValue().getFollowUpReference()

    # Finally, try to use the SLA parameter to guess where it could be
    elif 'project_guid' in filter_kw:
      kw['project_reference'] = filter_kw['project_guid']
    elif 'computer_guid' in filter_kw:
      computer_list = portal.portal_catalog(
        portal_type=['Compute Node', 'Remote Node', 'Instance Node'],
        reference=filter_kw['computer_guid'],
        limit=2
      )
      if len(computer_list) == 1:
        kw['project_reference'] = computer_list[0].getFollowUpReference()
    elif 'network_guid' in filter_kw:
      network_list = portal.portal_catalog(
        portal_type='Computer Network',
        reference=filter_kw['network_guid'],
        limit=2
      )
      if len(network_list) == 1:
        kw['project_reference'] = network_list[0].getFollowUpReference()


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
  return requested_software_instance.getSlapJSON()

return {
  'message': 'Software Instance Not Ready',
  'status': 102,
  'name': 'SoftwareInstanceNotReady'
}
