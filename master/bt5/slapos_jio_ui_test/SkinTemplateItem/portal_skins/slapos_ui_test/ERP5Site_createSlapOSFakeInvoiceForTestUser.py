from DateTime import DateTime

portal = context.getPortalObject()
accounting_module = portal.accounting_module
person_module = portal.person_module
#portal_membership=portal.portal_membership

one_hour = 1.0 / 24.0
today = DateTime(DateTime().Date()) + 8 * one_hour

if person_module.demo_user_invoice_functional is None:
  context.WebSection_newCredentialRequest(
    reference="demo_user_invoice_functional",
    default_email_text="demo@nexedi.com",
    first_name="Demo User",
    last_name="Functional",
    password="demo_user_invoice_functional",
    default_telephone_text="12345678",
    corporate_name="Nexedi",
    default_address_city="Campos",
    default_address_street_address="Av Pelinca",
    default_address_zip_code="28480",
    batch_mode=1
  )
#for person in person_module.objectValues():
#  if person.getTitle()=='Demo User Functional':
#    demo_user_functional=person

#demo_user_functional=portal_membership.getAuthenticatedMember().getUserValue()

accounting_module.newContent(
  portal_type='Sale Invoice Transaction',
  title='Fake Invoice for Demo User Invoice Functional',
  simulation_state='delivered',
  reference='1',
  destination_section_value='person_module/demo_user_invoice_functional',
  start_date=today,
)

return 'Done.'
