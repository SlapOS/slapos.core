portal = context.getPortalObject()

activate_kw = {'tag': tag, 'priority': 2}
portal.portal_catalog.searchAndActivate(
  portal_type='Project',
  validation_state='validated',
  method_id='Project_generateSubscriptionChangeRequestForProjectRelatedItem',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)

context.activate(after_tag=tag).getId()
