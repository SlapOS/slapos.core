portal = context.getPortalObject()

requester = portal.portal_membership.getAuthenticatedMember().getUserValue()
search_kw = {
  "portal_type": "Instance Tree",
  "validation_state": "validated",
  "destination_section__uid": requester.getUid(),
  "select_list": ("title",),
  "sort_on": [("title", "ASC")]
}

result_list = [{
  "title": x.title,
} for x in portal.portal_catalog(**search_kw)]

return {
  "result_list": result_list
}
