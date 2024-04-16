from zExceptions import Unauthorized
import json
edit_kw = {}

person = context.getPortalObject().portal_membership.getAuthenticatedMember().getUserValue()
if person != context.getParentValue():
  raise Unauthorized

original_login = context.getReference()

if reference is not None:
  edit_kw["reference"] = reference

if password is not None:
  edit_kw["password"] = password

if len(edit_kw):
  context.edit(**edit_kw)


# This will raise if login is duplicated. 
# XXX Improve this later by 
context.Base_checkConsistency()

current_username = context.getPortalObject().portal_membership.getAuthenticatedMember().getUserName()

if current_username == original_login:
  # We should logout immediately
  if 'portal_skin' in context.REQUEST:
    context.portal_skins.clearSkinCookie()
  context.REQUEST.RESPONSE.expireCookie('__ac', path='/')
  context.REQUEST.RESPONSE.expireCookie('__ac_google_hash', path='/')
  context.REQUEST.RESPONSE.expireCookie('__ac_facebook_hash', path='/')
  context.REQUEST.RESPONSE.setHeader('Location', context.getPermanentURL(context))
  context.REQUEST.RESPONSE.setStatus('303')
  
return json.dumps(context.getRelativeUrl())
