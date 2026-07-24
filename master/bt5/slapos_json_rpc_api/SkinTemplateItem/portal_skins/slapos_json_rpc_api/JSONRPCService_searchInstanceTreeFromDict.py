portal = context.getPortalObject()

search_kw = {
  "portal_type": "Instance Tree",
  "validation_state": "validated",
  "destination_section__uid": context.Base_getAuthenticatedPersonAndWorkgroupUidList(),
  "select_list": ("title",),
  "sort_on": [("title", "ASC")]
}

result_list = [{
  "title": x.title,
} for x in portal.portal_catalog(**search_kw)]

return {
  "result_list": result_list
}
