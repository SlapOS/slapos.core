portal = context.getPortalObject()


business_process_uid_list = [
  portal.business_process_module.slapos_subscription_business_process.getUid()]

subscription_delivery_specialise_uid_list = [q.getUid() for q in portal.portal_catalog(
  specialise_uid=business_process_uid_list, portal_type='Sale Trade Condition')]

search_kw = {
  'portal_type': 'Sale Packing List Line',
  'simulation_state': 'delivered',
  # Default Aggregate UID to the hosting subscription?
  "parent_specialise_uid": subscription_delivery_specialise_uid_list,
  'grouping_reference' : context.getReference()}

related_line_list = portal.portal_catalog(**search_kw)

if len(related_line_list) == 0:
  return context.Base_redirect(
         "view", keep_items={
           "portal_status_message": context.Base_translateString("No Packing List related.")}
       )
elif len(related_line_list) == 1:
  related_line_list[0].Base_redirect(
         "view", keep_items={
           "portal_status_message": context.Base_translateString("Related Grouped Sale Packing List")}
       )

else:
  selection_uid_list = [x.getUid() for x in related_line_list]
  message = context.Base_translateString(
      "Documents related to %s." % context.getPortalType(),
       # if not found, fallback to generic translation
      default=context.Base_translateString('Documents related to ${that_portal_type} : ${that_title}.',
        mapping={"that_portal_type": context.getTranslatedPortalType(),
                 "that_title": context.getTitleOrId() }),)
  return context.Base_redirect("Base_jumpToRelatedObjectList",
                keep_items=dict(reset=1,
                                uid=selection_uid_list,
                                portal_status_message=message))
