"""Fetch compute_node to find witch software is installed"""
portal_type = "Software Release"

url_string_list = context.ComputeNode_getSoftwareReleaseUrlStringList()
if url_string_list:
  return context.portal_catalog(
    portal_type=portal_type,
    url_string=url_string_list)
else:
  return []
