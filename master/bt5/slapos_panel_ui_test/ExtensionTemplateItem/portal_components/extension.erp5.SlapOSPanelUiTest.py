from Products.ERP5Security import SUPER_USER
from AccessControl.SecurityManagement import getSecurityManager, \
                                        setSecurityManager,  newSecurityManager
from erp5.component.module.DateUtils import getClosestDate, addToDate
from DateTime import DateTime

def ERP5Site_activateAlarmSlapOSPanelTest(self):
  portal = self.getPortalObject()
  sm = getSecurityManager()
  try:
    newSecurityManager(None, portal.acl_users.getUser(SUPER_USER))

    for alarm in portal.portal_alarms.contentValues():
      if alarm.isEnabled():
        alarm.activeSense()

  finally:
    setSecurityManager(sm)

  return "Alarms activated."


def ERP5Site_bootstrapSlapOSPanelTest(self, step, scenario, customer_login,
                                      manager_login, remote_customer_login,
                                      passwd, currency=None,
                                      project_title='Test Project'):

  if step not in ['trade_condition', 'account']:
    raise ValueError('Unsupported bootstrap step: %s' % step)

  if scenario not in ['accounting', 'customer', 'customer_shared',
                      'customer_remote']:
    raise ValueError('Unsupported bootstrap scenario: %s' % scenario)

  portal = self.getPortalObject()

  if step == 'trade_condition':
    #################################################
    # Bootstrap users
    #################################################
    sm = getSecurityManager()
    try:
      newSecurityManager(None, portal.acl_users.getUser(SUPER_USER))

      # Ensure checkConsistency is OK on the website installed by ui_test bt5
      portal.portal_alarms.upgrader_check_post_upgrade.activeSense(fixit=True)

      # Currency
      if currency is None:
        currency = portal.currency_module.newContent(
          portal_type="Currency",
          reference="test-currency-%s" % self.generateNewId(),
          short_title="tc%s" % self.generateNewId(),
          title="Test currency",
          base_unit_quantity=0.01
        )
        currency.validate()

      # Organisation
      organisation = portal.organisation_module.newContent(
        portal_type="Organisation",
        title="test-seller-%s" % self.generateNewId(),
        price_currency_value=currency,
        default_address_region='europe/west/france'
      )
      organisation.validate()
      seller_bank_account = organisation.newContent(
        portal_type="Bank Account",
        title="test_bank_account_%s" % self.generateNewId(),
        price_currency_value=currency
      )
      seller_bank_account.validate()

      # Sale Trade Condition for Tax
      sale_trade_condition = portal.sale_trade_condition_module.newContent(
        portal_type="Sale Trade Condition",
        reference="Tax/payment for: %s" % currency.getRelativeUrl(),
        trade_condition_type="default",
        # XXX hardcoded
        specialise="business_process_module/slapos_sale_subscription_business_process",
        price_currency_value=currency,
        payment_condition_payment_mode='test-%s' % self.generateNewId()
      )
      sale_trade_condition.newContent(
        portal_type="Trade Model Line",
        reference="VAT",
        resource="service_module/slapos_tax",
        base_application="base_amount/invoicing/taxable",
        trade_phase="slapos/tax",
        price=0.2,
        quantity=1.0,
        membership_criterion_base_category=('price_currency', 'base_contribution'),
        membership_criterion_category=('price_currency/%s' % currency.getRelativeUrl(), 'base_contribution/base_amount/invoicing/taxable')
      )
      sale_trade_condition.validate()

      # Normalise with SubscriptionRequest_createOpenSaleOrder
      effective_date = getClosestDate(target_date=DateTime(), precision='day')
      while effective_date.day() >= 29:
        effective_date = addToDate(effective_date, to_add={'day': -1})

      # Sale trade condition for project
      trade_condition = portal.sale_trade_condition_module.newContent(
        portal_type="Sale Trade Condition",
        reference="virtual master for %s" % organisation.getTitle(),
        trade_condition_type="virtual_master",
        specialise_value=sale_trade_condition,
        source_value=organisation,
        source_section_value=organisation if (scenario == 'accounting') else None,
        price_currency_value=currency,
        effective_date=effective_date
      )
      trade_condition.validate()

      if scenario == 'accounting':

        # Create trade condition for Deposit
        portal.sale_trade_condition_module.newContent(
          portal_type="Sale Trade Condition",
          reference="Deposit for : %s" % currency.getRelativeUrl(),
          trade_condition_type="deposit",
          specialise_value=sale_trade_condition,
          source_value=organisation,
          source_section_value=organisation,
          price_currency_value=currency).validate()

        # Sale Supply for Virtual Master
        sale_supply = portal.sale_supply_module.newContent(
          portal_type="Sale Supply",
          title="Sale Supply for Virtual Master (%s)" % currency.getRelativeUrl(),
          price_currency_value=currency,
        )
        sale_supply.newContent(
          portal_type="Sale Supply Line",
          base_price=24,
          resource="service_module/slapos_virtual_master_subscription"
        )
        sale_supply.validate()
    finally:
      setSecurityManager(sm)

  elif step == 'account':

    sm = getSecurityManager()
    try:
      newSecurityManager(None, portal.acl_users.getUser(SUPER_USER))

      # Fake user registrations

      # Bootstrap one manager user
      manager_person = portal.person_module.newContent(
        portal_type='Person',
        first_name='Manual test Project Manager',
        default_email_coordinate_text='romain+manager@nexedi.com',
        default_address_region='europe/west/france'
      )
      manager_person.newContent(
        portal_type='ERP5 Login',
        reference=manager_login,
        password=passwd
      ).validate()
      manager_person.validate()

      # Bootstrap one customer user
      customer_person = portal.person_module.newContent(
        portal_type='Person',
        first_name='Manual test Project Customer',
        default_email_coordinate_text='romain+customer@nexedi.com',
        default_address_region='europe/west/france'
      )
      customer_person.newContent(
        portal_type='ERP5 Login',
        reference=customer_login,
        password=passwd
      ).validate()
      customer_person.validate()

      if scenario == 'customer_remote':
        # Bootstrap one customer user for the remote project
        remote_customer_person = portal.person_module.newContent(
          portal_type='Person',
          first_name='Manual test Remote Project Customer',
          default_email_coordinate_text='romain+remote+customer@nexedi.com',
          default_address_region='europe/west/france'
        )
        remote_customer_person.newContent(
          portal_type='ERP5 Login',
          reference=remote_customer_login,
          password=passwd
        ).validate()
        remote_customer_person.validate()

      currency = portal.portal_catalog.getResultValue(
        portal_type="Currency",
        title="Test currency",
        sort_on=[['creation_date', 'DESC']]
      )

      # Create Project
      project = manager_person.Person_addVirtualMaster(
        project_title,
        scenario == 'accounting',
        scenario == 'accounting',
        currency.getRelativeUrl(),
        batch=1)

      if scenario == 'accounting':
        manager_person.newContent(
          portal_type='Assignment',
          title='Sale',
          function='sale/manager'
        ).open()

      customer_person.newContent(
        portal_type='Assignment',
        title='Customer for project %s' % project.getTitle(),
        destination_project_value=project,
        function='customer'
      ).open()

      # Ensure checkConsistency is OK on this preference
      preference = portal.portal_preferences.slapos_default_system_preference
      preference.edit(
        preferred_hateoas_url='.',
        preferred_subscription_assignment_category_list=[
          'function/customer',
          'role/client',
          'destination_project/%s' % project.getRelativeUrl()
        ]
      )

      if scenario == 'customer_shared':
        # XXX For shared instance, user must also be a customer
        # How to create Instance Node without any user related document?
        manager_person.newContent(
          portal_type='Assignment',
          title='Customer for project %s' % project.getTitle(),
          destination_project_value=project,
          function='customer'
        ).open()

      if scenario == 'customer_remote':
        remote_project = customer_person.Person_addVirtualMaster(
          'Test Remote Project',
          scenario == 'accounting',
          scenario == 'accounting',
          currency.getRelativeUrl(),
          batch=1)
        remote_customer_person.newContent(
          portal_type='Assignment',
          title='Customer for project %s' % remote_project.getTitle(),
          destination_project_value=remote_project,
          function='customer'
        ).open()


    finally:
      setSecurityManager(sm)

  return "Done."

