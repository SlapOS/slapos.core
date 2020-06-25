from DateTime import DateTime

portal = context.getPortalObject()
account_module = portal.account_module

one_hour = 1.0 / 24.0
today = DateTime(DateTime().Date()) + 8 * one_hour

context.AccountingTransactionModule_createAccountingTestDocument(
  portal_type='Sale Invoice Transaction',
  title='First One',
  simulation_state='cancelled',
  reference='1',
  destination_section_value=portal.organisation_module.client_1,
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
return 'ok'
