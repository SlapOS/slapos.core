slap_state = ['start_requested', 'stop_requested']
if not context.getSlapState() in slap_state:
  return None

software_instance_list = [q for q in context.getSuccessorValueList() if q.getSlapState() in slap_state]
if len(software_instance_list) == 0:
  return None
software_instance = software_instance_list[0]

software_release_list = context.SoftwareProduct_getSortedSoftwareReleaseList(
                          software_release_url=software_instance.getUrlString())

if not software_release_list:
  return None
latest_software_release = software_release_list[0]
if latest_software_release.getUrlString() == software_instance.getUrlString():
  return None
else:
  return latest_software_release
