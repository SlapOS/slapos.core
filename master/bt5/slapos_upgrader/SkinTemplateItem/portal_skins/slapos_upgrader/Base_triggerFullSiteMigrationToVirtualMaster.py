portal = context.getPortalObject()
tag = script.id

### Create the bootstrap Trade Condition
currency = portal.restrictedTraverse('currency_module/EUR')
seller_organisation = portal.restrictedTraverse('organisation_module/rapidspace')
business_process = portal.restrictedTraverse('business_process_module/slapos_sale_subscription_business_process')

if portal.portal_catalog.getResultValue(
  portal_type='Sale Trade Condition',
  specialise__uid=business_process.getUid()
) is None:
  # Sale Trade Condition for Tax
  sale_trade_condition = portal.sale_trade_condition_module.newContent(
    portal_type="Sale Trade Condition",
    reference="Tax/payment for: %s" % currency.getTitle(),
    trade_condition_type="default",
    # XXX hardcoded
    specialise_value=business_process,
    price_currency_value=currency
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
  sale_trade_condition.reindexObject(activate_kw={'tag': tag})

  # Create Trade Condition to create Project
  sale_trade_condition = portal.sale_trade_condition_module.newContent(
    portal_type="Sale Trade Condition",
    reference="%s-VirtualMaster" % seller_organisation.getTitle(),
    trade_condition_type="virtual_master",
    specialise_value=sale_trade_condition,
    source_value=seller_organisation,
    price_currency_value=currency,
  )
  sale_trade_condition.validate()
  sale_trade_condition.reindexObject(activate_kw={'tag': tag})

return context.activate(after_tag=tag, priority=4).Base_triggerFullSiteMigrationToVirtualMasterStep2()
