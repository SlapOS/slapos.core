portal = context.getPortalObject()

error_list = []
if context.getId() != "caucase_adapter":
  return error_list
caucase_service = portal.portal_web_services.caucase_adapter
promise_caucase_url = portal.getPromiseParameter('external_service', 'caucase_url')

if promise_caucase_url is not None:
  url_string = caucase_service.getUrlString()
  _, caucase_url = context.CaucaseRESTClient_getSecureServiceUrl(promise_caucase_url)
  if not url_string or not caucase_service.getPassword() \
      or not caucase_service.getUserId():
    error_list.append("Caucase web service is not configured!")
  elif caucase_url.rstrip('/') != url_string.rstrip('/'):
    # caucase URL was modified
    error_list.append(
      "Caucase web service is not configured as Expected: %s" %
        "Expect as url_string: %s\nGot %s" % (caucase_url, url_string))


if len(error_list) > 0 and fixit:
  context.CaucaseRESTClient_configureCaucase(promise_caucase_url)
return error_list
