grouping_reference = [ x.getGroupingReference() for x in context.objectValues() if x.getGroupingReference() is not None]

assert len(grouping_reference) in [0, 1], "Too many grouping references"

if not grouping_reference:
  return context.Base_redirect(
         "view", keep_items={
           "portal_status_message": context.Base_translateString("No Packing List related.")}
       )

aggregated_spl_list = context.getPortalObject().portal_catalog.getResultValue(
  portal_type="Sale Packing List",
  reference=grouping_reference)

if not aggregated_spl_list:
  return context.Base_redirect(
         "view", keep_items={
           "portal_status_message": context.Base_translateString("No Packing List related.")}
       )

return aggregated_spl_list.Base_redirect(
         "view", keep_items={
           "portal_status_message": context.Base_translateString("Related Sale Packing List Grouped")}
       )
