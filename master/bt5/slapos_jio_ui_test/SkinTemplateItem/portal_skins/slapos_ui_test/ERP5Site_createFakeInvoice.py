from DateTime import DateTime

portal = context.getPortalObject()
account_module = portal.account_module
portal_membership=portal.portal_membership

one_hour = 1.0 / 24.0
today = DateTime(DateTime().Date()) + 8 * one_hour

#for person in person_module.objectValues():
#  if person.getTitle()=='Demo User Functional':
#    demo_user_functional=person

demo_user_functional=portal_membership.getAuthenticatedMember().getUserValue()

context.AccountingTransactionModule_createAccountingTestDocument(
  portal_type='Sale Invoice Transaction',
  title='Fake Invoice',
  simulation_state='delivered',
  reference='1',
  destination_section_value=demo_user_functional,
  start_date=today,
  embedded=[
    {"portal_type": 'Sale Invoice Transaction Line',
     "source_value": account_module.receivable,
     "source_debit": 119.60},
    {"portal_type": 'Sale Invoice Transaction Line',
     "source_value": account_module.collected_vat,
     "source_credit": 19.60},
    {"portal_type": 'Sale Invoice Transaction Line',
     "source_value": account_module.goods_sales,
     "source_credit": 100.00},
  ]
)

return 'Done.'
