portal = context.getPortalObject()
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery

#############################################
# Search software product without price
missing_price_project_dict = {}

for sql_result in portal.portal_catalog(source_section__uid='%',
                                        portal_type='Sale Trade Condition'):
  sale_trade_condition = sql_result.getObject()

  for sql_result_2 in portal.portal_catalog(follow_up__uid=sale_trade_condition.getSourceProjectUid(),
                                            portal_type='Software Product'):
    software_product = sql_result_2.getObject()

    sale_supply_line = portal.portal_catalog.getResultValue(portal_type='Sale Supply Line',
                                                            resource__uid=software_product.getUid())

    if (sale_supply_line is None):
      if software_product.getFollowUp() not in missing_price_project_dict:
        missing_price_project_dict[software_product.getFollowUp()] = []
      missing_price_project_dict[software_product.getFollowUp()].append(software_product)


print '<h1>Missing price</h1>'
print '<ol>'

print_info_list = []
for _, software_product_list in missing_price_project_dict.items():
  print_info_list.append((software_product_list[0].getFollowUpTitle(), software_product_list))

print_info_list.sort()
for print_info in print_info_list:
  print '<li><p><b>%s</b></p><ul>' % print_info[0]
  for software_product in print_info[1]:
    print '<li><i><a href="%s">%s</a></i></li>' % (software_product.getRelativeUrl(), software_product.getTitle())
  print '</ul></li>'
print '</ol>'

#############################################
# Item without Subscription Request
orphaned_item_project_dict = {}

subscribed_uid_list = [x.uid for x in portal.portal_catalog(
  portal_type=["Instance Tree"],
  aggregate__related__portal_type="Subscription Request"
)]

sql_kw = {}
if subscribed_uid_list:
  sql_kw['uid'] = NegatedQuery(SimpleQuery(uid=subscribed_uid_list))
for sql_result in portal.portal_catalog(
  portal_type=["Instance Tree"],
  validation_state="validated",
  **sql_kw
):
  item = sql_result.getObject()
  if item.getFollowUp() not in orphaned_item_project_dict:
    orphaned_item_project_dict[item.getFollowUp()] = []
  orphaned_item_project_dict[item.getFollowUp()].append(item)

print '<h1>Subscription not created</h1>'
print '<ol>'

print_info_list = []
for _, item_list in orphaned_item_project_dict.items():
  print_info_list.append((item_list[0].getFollowUpTitle(), item_list))

print_info_list.sort()
for print_info in print_info_list:
  print '<li><p><b>%s</b></p><ul>' % print_info[0]
  for item in print_info[1]:
    product_dict = item.InstanceTree_getSoftwareProduct()
    if product_dict[0] is not None:
      product_title = product_dict[0].getTitle()
    else:
      product_title = ""
    print '<li><i><a href="%s">%s</a></i> (%s)</li>' % (item.getRelativeUrl(), item.getTitle(), product_title)
  print '</ul></li>'
print '</ol>'

context.REQUEST.RESPONSE.setHeader('Content-Type', 'text/html')
return printed
