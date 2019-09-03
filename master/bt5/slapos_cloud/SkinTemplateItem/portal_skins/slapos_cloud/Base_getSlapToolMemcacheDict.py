from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

return context.getPortalObject().portal_memcached.getMemcachedDict(
  key_prefix='slap_tool',
  plugin_path='portal_memcached/default_memcached_plugin')
