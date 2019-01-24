network = context
portal = context.getPortalObject()
software_release = context.REQUEST.get('here')
if software_release is None or software_release.portal_type != 'Software Release':
  software_release = portal.portal_catalog.getResultValue(
    portal_type='Software Release',
    url_string=software_release_url,
  )

return sum([computer.Computer_getSoftwareReleaseFreePartitionCount(software_release.getUrlString())
            for computer in network.getSubordinationRelatedValueList()
            if computer.getAllocationScope() in ['open/public']])
