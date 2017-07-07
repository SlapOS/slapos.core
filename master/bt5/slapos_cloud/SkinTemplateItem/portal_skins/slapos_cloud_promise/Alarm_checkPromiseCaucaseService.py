from Products.CMFActivity.ActiveResult import ActiveResult

portal = context.getPortalObject()

severity = 0
summary = "Nothing to do."
detail = ""
if getattr(portal, 'portal_web_services', None) is not None and \
  getattr(portal.portal_web_services, 'caucase_adapter', None) is not None:
  promise_caucase_url = portal.getPromiseParameter('external_service', 'caucase_url')
  if promise_caucase_url is not None:
    caucase_service = portal.portal_web_services.caucase_adapter
    url_string = caucase_service.getUrlString()
    _, caucase_url = context.CaucaseRESTClient_getSecureServiceUrl(promise_caucase_url)
    if not url_string or not caucase_service.getPassword() \
       or not caucase_service.getUserId():
      severity = 1
      summary = "Caucase web service is not configured!"
      detail = ""
    elif caucase_url.rstrip('/') != url_string.rstrip('/'):
      # caucase URL was modified
      severity = 1
      summary = "Caucase web service is not configured as Expected"
      detail = "Expect as url_string: %s\nGot %s" % (caucase_url, url_string)

active_result = ActiveResult()
active_result.edit(
  summary=summary, 
  severity=severity,
  detail=detail)

context.newActiveProcess().postResult(active_result)
