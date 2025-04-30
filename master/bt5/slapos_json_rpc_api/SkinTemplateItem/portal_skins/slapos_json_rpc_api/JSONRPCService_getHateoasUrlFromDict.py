# from Products.ERP5Type.Cache import CachingMethod
from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError

class HateoasNotConfiguredError(JsonRpcAPIError):
  type = "HATEOAS-URL-NOT-FOUND"
  status = 403

preference_tool = context.getPortalObject().portal_preferences

"""
url = CachingMethod(preference_tool.getPreferredHateoasUrl,
  id='getHateoasUrl',
  cache_factory='slap_cache_factory')()
"""
url = preference_tool.getPreferredHateoasUrl()

if not url:
  raise HateoasNotConfiguredError('The hateoas url is not configured')

return {
  "hateoas_url": url
}
