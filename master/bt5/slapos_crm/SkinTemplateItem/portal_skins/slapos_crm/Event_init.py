"""Owner Proxy Role allows anonymous users to create events
through web sites.
"""
portal = context.getPortalObject()
# Set preferred text format and reference
context.setContentType(portal.portal_preferences.getPreferredTextFormat())
context.Event_generateReference()
context.edit(start_date=DateTime())
