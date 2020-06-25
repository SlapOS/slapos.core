from DateTime import DateTime

portal = context.getPortalObject()
accounting_module = portal.accounting_module
portal_membership=portal.portal_membership

demo_user_functional=portal_membership.getAuthenticatedMember().getUserValue()

accounting_module.newContent(
  portal_type='Sale Invoice Transaction',
  title='Fake Invoice for Demo User Functional',
  simulation_state='delivered',
  reference='1',
  destination_section_value=demo_user_functional,
  start_date=DateTime('2019/10/20'),
)

return 'Done.'
