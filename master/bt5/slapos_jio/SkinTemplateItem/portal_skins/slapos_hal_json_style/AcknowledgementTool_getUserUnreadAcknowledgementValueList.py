"""
Return the list of unread acknowledgements for the  user currently
connected. This script will use efficiently caches in order to slow
down as less a possible the user interface
"""
from DateTime import DateTime
portal = context.getPortalObject()

user_name = portal.portal_membership.getAuthenticatedMember().getId()

def getUnreadAcknowledgementListForUser(user_name=None):
  # We give the portal type "Mass Notification" for now, we can
  # have a getPortalAcknowledgeableTypeList method in the future
  portal_acknowledgements = getattr(portal, "portal_acknowledgements", None)
  result = []
  if portal_acknowledgements is not None:
    result = portal_acknowledgements.getUnreadDocumentUrlList(
                user_name=user_name, portal_type="Site Message")
  return result

from Products.ERP5Type.Cache import CachingMethod

# Cache for every user the list of url of not acknowledge documents
getUnreadAcknowledgementList = CachingMethod(getUnreadAcknowledgementListForUser,
                                        "getUnreadAcknowledgementListForUser")

return_list = []
url_list = getUnreadAcknowledgementList(user_name=user_name)
# For every not acknowledge document, check that documents are still not
# acknowledged and return them for the user interface
if len(url_list) > 0:
  return portal.portal_acknowledgements.getUnreadAcknowledgementList(
		  url_list=url_list, user_name=user_name)

return return_list
