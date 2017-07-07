portal = context.getPortalObject()

if getattr(portal, 'portal_web_services', None) is not None and \
    getattr(portal.portal_web_services, 'caucase_adapter', None) is not None:

  caucase_service = portal.portal_web_services.caucase_adapter
  promise_caucase_url = portal.getPromiseParameter('external_service', 'caucase_url')
  if promise_caucase_url is not None:
    caucase_service.CaucaseRESTClient_configureCaucase(promise_caucase_url)
