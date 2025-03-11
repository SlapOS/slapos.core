# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, TemporaryAlarmScript
from DateTime import DateTime

def convertCategoryList(base, l):
  return ['%s/%s' % (base, q) for q in l]


class TestSlapOSBuilderMixin(SlapOSTestCaseMixin):
  require_certificate = 1

  def addServiceSetup(self):
    """ Just an additional service added to movement to validate it works """
    service = self.portal.service_module.newContent(
      title="Instance Setup %s " % self.generateNewId(),
      reference="ISETUP-%s" % self.generateNewId(),
      use='trade/sale',
    )
    service.validate()
    return service

  def checkSimulationMovement(self, simulation_movement):
    self.assertEqual(1.0, simulation_movement.getDeliveryRatio())
    self.assertEqual(0.0, simulation_movement.getDeliveryError())
    self.assertNotEqual(None, simulation_movement.getDeliveryValue())

  def checkDeliveryLine(self, simulation_movement, delivery_line,
      line_portal_type, cell_portal_type):
    self.assertEqual(line_portal_type, delivery_line.getPortalType())
    self.assertSameSet([simulation_movement.getRelativeUrl()],
        delivery_line.getDeliveryRelatedList(
            portal_type='Simulation Movement'))
    self.assertSameSet([delivery_line.getRelativeUrl()],
        simulation_movement.getDeliveryList())
    self.assertSameSet([
        'use/trade/sale',
        'base_contribution/base_amount/invoicing/discounted',
        'base_contribution/base_amount/invoicing/taxable'] \
          + convertCategoryList('quantity_unit',
            simulation_movement.getQuantityUnitList())
          + convertCategoryList('aggregate',
            simulation_movement.getAggregateList())
          + convertCategoryList('resource',
            simulation_movement.getResourceList()),
      delivery_line.getCategoryList(),
      '%s %s' % (simulation_movement.getRelativeUrl(), delivery_line.getRelativeUrl())
    )
    self.assertEqual(simulation_movement.getQuantity(),
        delivery_line.getQuantity())
    self.assertEqual(simulation_movement.getPrice(),
        delivery_line.getPrice())
    self.assertFalse(delivery_line.hasStartDate())
    self.assertFalse(delivery_line.hasStopDate())
    self.assertEqual([], delivery_line.contentValues(
        portal_type=cell_portal_type))

  def checkDelivery(self, simulation_movement, delivery, delivery_portal_type,
        category_list, simulation_state='delivered', already_solved=False,
        expected_start_date=None, expected_stop_date=None):
    self.assertEqual(delivery_portal_type, delivery.getPortalType())
    self.assertEqual(simulation_state, delivery.getSimulationState())
    if not already_solved:
      self.assertEqual('building', delivery.getCausalityState())
      delivery.updateCausalityState(solve_automatically=False)
    self.assertEqual('solved', delivery.getCausalityState())
    self.assertTrue(delivery.hasStartDate())
    self.assertTrue(delivery.hasStopDate())
    if expected_start_date is None:
      expected_start_date = simulation_movement.getStartDate()
    self.assertEqual(expected_start_date, delivery.getStartDate())
    self.assertEqual(simulation_movement.getStartDate(), delivery.getStartDate())

    if expected_stop_date is None:
      expected_stop_date = simulation_movement.getStopDate()
    self.assertEqual(expected_stop_date, delivery.getStopDate())
    self.assertEqual(simulation_movement.getStopDate(), delivery.getStopDate())

    self.assertSameSet([
          'ledger/automated'] \
            + convertCategoryList('price_currency',
                simulation_movement.getPriceCurrencyList()) \
            + convertCategoryList('specialise',
                simulation_movement.getSpecialiseList()) \
            + convertCategoryList('source',
                simulation_movement.getSourceList()) \
            + convertCategoryList('source_section',
                simulation_movement.getSourceSectionList()) \
            + convertCategoryList('source_payment',
                simulation_movement.getSourcePaymentList()) \
            + convertCategoryList('destination',
                simulation_movement.getDestinationList()) \
            + convertCategoryList('destination_section',
                simulation_movement.getDestinationSectionList()) \
            + convertCategoryList('destination_decision',
                simulation_movement.getDestinationDecisionList()) \
            + convertCategoryList('destination_project',
                simulation_movement.getDestinationProjectList()) \
            + category_list,
      delivery.getCategoryList())


class TestSlapOSSalePackingListBuilder(TestSlapOSBuilderMixin):

  def test_sale_packing_list_builder(self):
    resource, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(is_accountable=True)
    project = instance_tree.getFollowUpValue()
    trade_condition = project.getSourceProjectRelatedValue(portal_type="Sale Trade Condition")
    currency = trade_condition.getPriceCurrencyValue()
    source = trade_condition.getSourceSectionValue()
    destination = instance_tree.getDestinationSectionValue()
    business_process = trade_condition.getSpecialiseValue()

    applied_rule = self.portal.portal_simulation.newContent(
      portal_type='Applied Rule',
      causality=instance_tree.getRelativeUrl(),
      specialise='portal_rules/slapos_subscription_item_rule'
    )

    simulation_movement_kw = dict(
        portal_type='Simulation Movement',
        aggregate_value=instance_tree,
        base_contribution=['base_amount/invoicing/discounted',
            'base_amount/invoicing/taxable'],
        causality=[
          '%s/deliver' % business_process.getRelativeUrl(),
          '%s/delivery_path' % business_process.getRelativeUrl()
        ],
        destination_value=destination,
        destination_decision_value=destination,
        destination_section_value=destination,
        destination_project_value=project,
        price_currency_value=currency,
        quantity_unit=resource.getQuantityUnit(),
        resource_value=resource,
        source_value=source,
        source_section_value=source,
        specialise_value=trade_condition,
        ledger='automated',
        trade_phase='slapos/delivery',
        use='trade/sale',
    )
    simulation_movement_1 = applied_rule.newContent(
        quantity=1.2,
        price=3.4,
        start_date=DateTime('2012/01/01'),
        stop_date=DateTime('2012/02/01'),
        **simulation_movement_kw
    )
    simulation_movement_2 = applied_rule.newContent(
        quantity=5.6,
        price=7.8,
        start_date=DateTime('2012/03/01'),
        stop_date=DateTime('2012/04/01'),
        **simulation_movement_kw
    )

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
      self.portal.portal_deliveries.slapos_sale_packing_list_builder.build(
          path='%s/%%' % applied_rule.getPath())
      self.tic()

    self.checkSimulationMovement(simulation_movement_1)
    self.checkSimulationMovement(simulation_movement_2)

    delivery_line_1 = simulation_movement_1.getDeliveryValue()
    delivery_line_2 = simulation_movement_2.getDeliveryValue()
    self.assertNotEqual(delivery_line_1.getRelativeUrl(),
        delivery_line_2.getRelativeUrl())

    line_kw = dict(line_portal_type='Sale Packing List Line',
        cell_portal_type='Sale Packing List Cell')
    self.checkDeliveryLine(simulation_movement_1, delivery_line_1, **line_kw)
    self.checkDeliveryLine(simulation_movement_2, delivery_line_2, **line_kw)

    delivery_1 = delivery_line_1.getParentValue()
    delivery_2 = delivery_line_2.getParentValue()

    self.assertNotEqual(delivery_1.getRelativeUrl(),
        delivery_2.getRelativeUrl())

    delivery_kw = dict(delivery_portal_type='Sale Packing List',
        category_list=convertCategoryList('causality',
          simulation_movement_1.getParentValue().getCausalityList()))
    self.checkDelivery(simulation_movement_1, delivery_1, **delivery_kw)
    self.checkDelivery(simulation_movement_2, delivery_2, **delivery_kw)


class TestSlapOSSaleInvoiceBuilder(TestSlapOSBuilderMixin):

  def test_sale_invoice_builder(self, causality1=None, causality2=None): # pylint: disable=arguments-differ
    resource, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(is_accountable=True)
    service_setup = self.addServiceSetup()
    project = instance_tree.getFollowUpValue()
    trade_condition = project.getSourceProjectRelatedValue(portal_type="Sale Trade Condition")
    currency = trade_condition.getPriceCurrencyValue()
    source = trade_condition.getSourceSectionValue()
    source_payment = trade_condition.getSourcePaymentValue()
    destination = instance_tree.getDestinationSectionValue()
    business_process = trade_condition.getSpecialiseValue()

    # Create Aggregated Packing List
    delivery_kw = dict(
        portal_type='Sale Packing List',
        price_currency_value=currency,
        source_value=source,
        source_section_value=source,
        source_payment_value=source_payment,
        specialise_value=trade_condition,
        ledger='automated'
    )
    delivery_line_kw = dict(
        portal_type='Sale Packing List Line',
        resource_value=resource,
        use='trade/sale',
        quantity_unit=resource.getQuantityUnit(),
        base_contribution_list=['base_amount/invoicing/discounted',
            'base_amount/invoicing/taxable'],
    )
    delivery_1 = self.portal.sale_packing_list_module.newContent(
        destination_value=destination,
        destination_decision_value=destination,
        destination_section_value=destination,
        destination_project_value=project,
        start_date=DateTime('2012/01/01'),
        stop_date=DateTime('2012/02/01'),
        causality_value=causality1,
        **delivery_kw
    )

    # Create Applied rule and set causality
    applied_rule_1 = self.portal.portal_simulation.newContent(
      portal_type='Applied Rule',
      specialise='portal_rules/slapos_delivery_root_simulation_rule',
      causality=delivery_1.getRelativeUrl()
    )
    self.portal.portal_workflow._jumpToStateFor(delivery_1, 'delivered')
    self.portal.portal_workflow._jumpToStateFor(delivery_1, 'calculating')
    if delivery_1.getCausalityState() == 'draft':
      # There are more than one workflow that has calculating state
      delivery_1.startBuilding()

    delivery_line_1 = delivery_1.newContent(
        quantity=1.2,
        price=3.4,
        **delivery_line_kw
    )
    delivery_line_1_bis = delivery_line_1.Base_createCloneDocument(
        batch_mode=1)
    delivery_line_1_bis.edit(
        price=0.0,
        resource_value=service_setup,
        quantity_unit='unit/piece'
    )

    # Create second delivery
    delivery_2 = self.portal.sale_packing_list_module.newContent(
        destination_value=destination,
        destination_decision_value=destination,
        destination_section_value=destination,
        destination_project_value=project,
        start_date=DateTime('2012/01/01'),
        stop_date=DateTime('2012/02/01'),
        causality_value=causality2,
        **delivery_kw
    )
    applied_rule_2 = self.portal.portal_simulation.newContent(
      portal_type='Applied Rule',
      specialise='portal_rules/slapos_delivery_root_simulation_rule',
      causality=delivery_2.getRelativeUrl()
    )
    self.portal.portal_workflow._jumpToStateFor(delivery_2, 'delivered')
    self.portal.portal_workflow._jumpToStateFor(delivery_2, 'calculating')
    if delivery_2.getCausalityState() == 'draft':
      # There are more than one workflow that has calculating state
      delivery_2.startBuilding()

    delivery_line_2 = delivery_2.newContent(
        quantity=5.6,
        price=7.8,
        **delivery_line_kw
    )
    simulation_movement_kw = dict(
        portal_type='Simulation Movement',
        base_contribution=['base_amount/invoicing/discounted',
            'base_amount/invoicing/taxable'],
        causality=[
          '%s/deliver' % business_process.getRelativeUrl(),
          '%s/delivery_path' % business_process.getRelativeUrl()],
        destination_value=destination,
        destination_decision_value=destination,
        destination_section_value=destination,
        destination_project_value=project,
        price_currency_value=currency,
        quantity_unit=resource.getQuantityUnit(),
        resource_value=resource,
        source_value=source,
        source_section_value=source,
        source_payment_value=source_payment,
        specialise_value=trade_condition,
        trade_phase='slapos/delivery',
        ledger='automated',
        use='trade/sale',
        delivery_ratio=1.0
    )
    simulation_movement_1 = applied_rule_1.newContent(
        quantity=delivery_line_1.getQuantity(),
        price=delivery_line_1.getPrice(),
        start_date=delivery_1.getStartDate(),
        stop_date=delivery_1.getStopDate(),
        delivery=delivery_line_1.getRelativeUrl(),
        **simulation_movement_kw
    )
    simulation_movement_1_bis = applied_rule_1.newContent(
        quantity=delivery_line_1_bis.getQuantity(),
        price=delivery_line_1_bis.getPrice(),
        start_date=delivery_1.getStartDate(),
        stop_date=delivery_1.getStopDate(),
        delivery=delivery_line_1_bis.getRelativeUrl(),
        **simulation_movement_kw
    )
    simulation_movement_1_bis.edit(
      resource=delivery_line_1_bis.getResource(),
      quantity_unit=delivery_line_1_bis.getQuantityUnit()
    )
    simulation_movement_2 = applied_rule_2.newContent(
        quantity=delivery_line_2.getQuantity(),
        price=delivery_line_2.getPrice(),
        start_date=delivery_2.getStartDate(),
        stop_date=delivery_2.getStopDate(),
        delivery=delivery_line_2.getRelativeUrl(),
        **simulation_movement_kw
    )

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual('calculating', delivery_1.getCausalityState())
    self.assertEqual('calculating', delivery_2.getCausalityState())

    delivery_1.updateCausalityState(solve_automatically=False)
    delivery_2.updateCausalityState(solve_automatically=False)
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

    # test the test
    self.assertEqual('solved', delivery_1.getCausalityState())
    self.assertEqual('solved', delivery_2.getCausalityState())

    # create new simulation movements
    invoice_movement_kw = simulation_movement_kw.copy()
    invoice_movement_kw.update(
        causality=[
            '%s/invoice' % business_process.getRelativeUrl(),
            '%s/invoice_path' % business_process.getRelativeUrl()
        ],
        trade_phase='slapos/invoicing'
    )
    invoice_rule_1 = simulation_movement_1.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_1 = invoice_rule_1.newContent(
        start_date=delivery_1.getStartDate(),
        stop_date=delivery_1.getStopDate(),
        quantity=delivery_line_1.getQuantity(),
        price=delivery_line_1.getPrice(),
        **invoice_movement_kw)

    invoice_rule_1_bis = simulation_movement_1_bis.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_1_bis = invoice_rule_1_bis.newContent(
        start_date=delivery_1.getStartDate(),
        stop_date=delivery_1.getStopDate(),
        quantity=delivery_line_1_bis.getQuantity(),
        price=delivery_line_1_bis.getPrice(),
        **invoice_movement_kw)
    invoice_movement_1_bis.edit(
      resource=delivery_line_1_bis.getResource(),
      quantity_unit=delivery_line_1_bis.getQuantityUnit()
    )

    invoice_rule_2 = simulation_movement_2.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_2 = invoice_rule_2.newContent(
        start_date=delivery_2.getStartDate(),
        stop_date=delivery_2.getStopDate(),
        quantity=delivery_line_2.getQuantity(),
        price=delivery_line_2.getPrice(),
        **invoice_movement_kw)

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

      self.portal.portal_deliveries.slapos_sale_invoice_builder.build(
          path=['%s/%%' % applied_rule_1.getPath(),
                '%s/%%' % applied_rule_2.getPath()])
      self.tic()

    self.checkSimulationMovement(invoice_movement_1)
    self.checkSimulationMovement(invoice_movement_1_bis)
    self.checkSimulationMovement(invoice_movement_2)

    invoice_line_1 = invoice_movement_1.getDeliveryValue()
    invoice_line_1_bis = invoice_movement_1_bis.getDeliveryValue()
    invoice_line_2 = invoice_movement_2.getDeliveryValue()
    self.assertNotEqual(invoice_line_1.getRelativeUrl(),
        invoice_line_2.getRelativeUrl())
    self.assertNotEqual(invoice_line_1, invoice_line_1_bis)
    self.assertEqual(invoice_line_1.getParentValue(),
        invoice_line_1_bis.getParentValue())

    line_kw = dict(line_portal_type='Invoice Line',
        cell_portal_type='Invoice Cell')
    self.checkDeliveryLine(invoice_movement_1, invoice_line_1, **line_kw)
    self.checkDeliveryLine(invoice_movement_1_bis, invoice_line_1_bis,
        **line_kw)
    self.checkDeliveryLine(invoice_movement_2, invoice_line_2, **line_kw)

    invoice_1 = invoice_line_1.getParentValue()
    invoice_2 = invoice_line_2.getParentValue()

    # The invoices are merged since they are from the same user.
    self.assertEqual(invoice_1.getRelativeUrl(),
        invoice_2.getRelativeUrl())

    invoice_kw = dict(delivery_portal_type='Sale Invoice Transaction',
        simulation_state='confirmed')
    category_list = ['resource/%s' % currency.getRelativeUrl()]
    self.checkDelivery(invoice_movement_1, invoice_1,
        category_list=category_list + convertCategoryList('causality',
          [delivery_1.getRelativeUrl(), delivery_2.getRelativeUrl()]), **invoice_kw)

    # Start building and check again, remember invoice_1 and invoice_2 
    invoice_1.startBuilding()
    self.checkDelivery(invoice_movement_2, invoice_2,
        category_list=category_list + convertCategoryList('causality',
          [delivery_1.getRelativeUrl(), delivery_2.getRelativeUrl()]), **invoice_kw)

    # check delivering of movement later
    delivery_line_2_bis = delivery_line_2.Base_createCloneDocument(
        batch_mode=1)
    delivery_line_2_bis.edit(
        # Keep price different else this line will be merged with delivery_line_1_bis
        # on the invoice side
        price=1.1,
        resource_value=service_setup,
        quantity_unit='unit/piece'
    )
    simulation_movement_2_bis = applied_rule_2.newContent(
        quantity=delivery_line_2_bis.getQuantity(),
        price=delivery_line_2_bis.getPrice(),
        start_date=delivery_2.getStartDate(),
        stop_date=delivery_2.getStopDate(),
        delivery=delivery_line_2_bis.getRelativeUrl(),
        **simulation_movement_kw
    )
    simulation_movement_2_bis.edit(
      resource=delivery_line_2_bis.getResource(),
      quantity_unit=delivery_line_2_bis.getQuantityUnit()
    )
    invoice_rule_2_bis = simulation_movement_2_bis.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_2_bis = invoice_rule_2_bis.newContent(
        start_date=delivery_2.getStartDate(),
        stop_date=delivery_2.getStopDate(),
        quantity=delivery_line_2_bis.getQuantity(),
        price=delivery_line_2_bis.getPrice(),
        **invoice_movement_kw)
    invoice_movement_2_bis.edit(
      resource=delivery_line_2_bis.getResource(),
      quantity_unit=delivery_line_2_bis.getQuantityUnit()
    )

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
      # test the test
      delivery_2.updateCausalityState(solve_automatically=False)
      self.tic()
      self.assertEqual('solved', delivery_2.getCausalityState())

      self.assertEqual(invoice_movement_2_bis.getDeliveryValue(), None)
      self.portal.portal_deliveries.slapos_sale_invoice_builder.build(
          path='%s/%%' % applied_rule_1.getPath())

      self.assertEqual(invoice_movement_2_bis.getDeliveryValue(), None)
      self.portal.portal_deliveries.slapos_sale_invoice_builder.build(
        path='%s/%%' % applied_rule_2.getPath())
      self.tic()

    self.checkSimulationMovement(invoice_movement_2_bis)
    invoice_line_2_bis = invoice_movement_2_bis.getDeliveryValue()
    self.assertNotEqual(invoice_line_2, invoice_line_2_bis)
    self.assertEqual(invoice_line_2.getParentValue(),
        invoice_line_2_bis.getParentValue())
    self.checkDeliveryLine(invoice_movement_2_bis, invoice_line_2_bis,
        **line_kw)
    self.checkDelivery(invoice_movement_2_bis, invoice_2,
        category_list=category_list + convertCategoryList('causality',
          [delivery_1.getRelativeUrl(), delivery_2.getRelativeUrl()]), **invoice_kw)
    self.assertEqual(
      invoice_line_2.getParentValue(), invoice_line_1.getParentValue()
    )

  def test_sale_invoice_builder_with_same_causality(self):
    causality1 = self.portal.subscription_request_module.newContent(
      portal_type="Subscription Request", 
    )
    self.test_sale_invoice_builder(causality1=causality1, causality2=causality1) 


  def test_sale_invoice_builder_with_different_causality(self):
    causality1 = self.portal.subscription_request_module.newContent(
      portal_type="Subscription Request", 
    )
    causality2 = self.portal.subscription_request_module.newContent(
      portal_type="Subscription Request", 
    )
    self.test_sale_invoice_builder(causality1=causality1, causality2=causality2) 

  def test_sale_invoice_builder_with_ssingle_ausality(self):
    causality1 = self.portal.subscription_request_module.newContent(
      portal_type="Subscription Request", 
    )
    self.test_sale_invoice_builder(causality1=causality1, causality2=None) 

  def test_sale_invoice_builder_with_different_date(self):
    resource, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(is_accountable=True)
    service_setup = self.addServiceSetup()
    project = instance_tree.getFollowUpValue()
    trade_condition = project.getSourceProjectRelatedValue(portal_type="Sale Trade Condition")
    currency = trade_condition.getPriceCurrencyValue()
    source = trade_condition.getSourceSectionValue()
    destination = instance_tree.getDestinationSectionValue()
    business_process = trade_condition.getSpecialiseValue()

    # Create Aggregated Packing List
    delivery_kw = dict(
        portal_type='Sale Packing List',
        price_currency_value=currency,
        source_value=source,
        source_section_value=source,
        specialise_value=trade_condition,
        ledger='automated'
    )
    delivery_line_kw = dict(
        portal_type='Sale Packing List Line',
        resource_value=resource,
        use='trade/sale',
        quantity_unit=resource.getQuantityUnit(),
        base_contribution_list=['base_amount/invoicing/discounted',
            'base_amount/invoicing/taxable'],
    )
    delivery_1 = self.portal.sale_packing_list_module.newContent(
        destination_value=destination,
        destination_decision_value=destination,
        destination_section_value=destination,
        destination_project_value=project,
        start_date=DateTime('2012/01/01'),
        stop_date=DateTime('2012/02/01'),
        **delivery_kw
    )

    # Create Applied rule and set causality
    applied_rule_1 = self.portal.portal_simulation.newContent(
      portal_type='Applied Rule',
      specialise='portal_rules/slapos_delivery_root_simulation_rule',
      causality=delivery_1.getRelativeUrl()
    )
    self.portal.portal_workflow._jumpToStateFor(delivery_1, 'delivered')
    self.portal.portal_workflow._jumpToStateFor(delivery_1, 'calculating')
    if delivery_1.getCausalityState() == 'draft':
      # There are more than one workflow that has calculating state
      delivery_1.startBuilding()

    delivery_line_1 = delivery_1.newContent(
        quantity=1.2,
        price=3.4,
        **delivery_line_kw
    )
    delivery_line_1_bis = delivery_line_1.Base_createCloneDocument(
        batch_mode=1)
    delivery_line_1_bis.edit(
        price=0.0,
        resource_value=service_setup,
        quantity_unit='unit/piece'
    )

    # Create second delivery
    delivery_2 = self.portal.sale_packing_list_module.newContent(
        destination_value=destination,
        destination_decision_value=destination,
        destination_section_value=destination,
        destination_project_value=project,
        start_date=DateTime('2012/02/01'),
        stop_date=DateTime('2012/03/01'),
        **delivery_kw
    )
    applied_rule_2 = self.portal.portal_simulation.newContent(
      portal_type='Applied Rule',
      specialise='portal_rules/slapos_delivery_root_simulation_rule',
      causality=delivery_2.getRelativeUrl()
    )
    self.portal.portal_workflow._jumpToStateFor(delivery_2, 'delivered')
    self.portal.portal_workflow._jumpToStateFor(delivery_2, 'calculating')
    if delivery_2.getCausalityState() == 'draft':
      # There are more than one workflow that has calculating state
      delivery_2.startBuilding()

    delivery_line_2 = delivery_2.newContent(
        quantity=5.6,
        price=7.8,
        **delivery_line_kw
    )
    simulation_movement_kw = dict(
        portal_type='Simulation Movement',
        base_contribution=['base_amount/invoicing/discounted',
            'base_amount/invoicing/taxable'],
        causality=[
          '%s/deliver' % business_process.getRelativeUrl(),
          '%s/delivery_path' % business_process.getRelativeUrl()],
        destination_value=destination,
        destination_decision_value=destination,
        destination_section_value=destination,
        destination_project_value=project,
        price_currency_value=currency,
        quantity_unit=resource.getQuantityUnit(),
        resource_value=resource,
        source_value=source,
        source_section_value=source,
        specialise_value=trade_condition,
        trade_phase='slapos/delivery',
        ledger='automated',
        use='trade/sale',
        delivery_ratio=1.0
    )
    simulation_movement_1 = applied_rule_1.newContent(
        quantity=delivery_line_1.getQuantity(),
        price=delivery_line_1.getPrice(),
        start_date=delivery_1.getStartDate(),
        stop_date=delivery_1.getStopDate(),
        delivery=delivery_line_1.getRelativeUrl(),
        **simulation_movement_kw
    )
    simulation_movement_1_bis = applied_rule_1.newContent(
        quantity=delivery_line_1_bis.getQuantity(),
        price=delivery_line_1_bis.getPrice(),
        start_date=delivery_1.getStartDate(),
        stop_date=delivery_1.getStopDate(),
        delivery=delivery_line_1_bis.getRelativeUrl(),
        **simulation_movement_kw
    )
    simulation_movement_1_bis.edit(
      resource=delivery_line_1_bis.getResource(),
      quantity_unit=delivery_line_1_bis.getQuantityUnit()
    )
    simulation_movement_2 = applied_rule_2.newContent(
        quantity=delivery_line_2.getQuantity(),
        price=delivery_line_2.getPrice(),
        start_date=delivery_2.getStartDate(),
        stop_date=delivery_2.getStopDate(),
        delivery=delivery_line_2.getRelativeUrl(),
        **simulation_movement_kw
    )

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual('calculating', delivery_1.getCausalityState())
    self.assertEqual('calculating', delivery_2.getCausalityState())

    delivery_1.updateCausalityState(solve_automatically=False)
    delivery_2.updateCausalityState(solve_automatically=False)
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

    # test the test
    self.assertEqual('solved', delivery_1.getCausalityState())
    self.assertEqual('solved', delivery_2.getCausalityState())

    # create new simulation movements
    invoice_movement_kw = simulation_movement_kw.copy()
    invoice_movement_kw.update(
        causality=[
            '%s/invoice' % business_process.getRelativeUrl(),
            '%s/invoice_path' % business_process.getRelativeUrl()
        ],
        trade_phase='slapos/invoicing'
    )
    invoice_rule_1 = simulation_movement_1.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_1 = invoice_rule_1.newContent(
        start_date=delivery_1.getStartDate(),
        stop_date=delivery_1.getStopDate(),
        quantity=delivery_line_1.getQuantity(),
        price=delivery_line_1.getPrice(),
        **invoice_movement_kw)

    invoice_rule_1_bis = simulation_movement_1_bis.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_1_bis = invoice_rule_1_bis.newContent(
        start_date=delivery_1.getStartDate(),
        stop_date=delivery_1.getStopDate(),
        quantity=delivery_line_1_bis.getQuantity(),
        price=delivery_line_1_bis.getPrice(),
        **invoice_movement_kw)
    invoice_movement_1_bis.edit(
      resource=delivery_line_1_bis.getResource(),
      quantity_unit=delivery_line_1_bis.getQuantityUnit()
    )

    invoice_rule_2 = simulation_movement_2.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_2 = invoice_rule_2.newContent(
        start_date=delivery_2.getStartDate(),
        stop_date=delivery_2.getStopDate(),
        quantity=delivery_line_2.getQuantity(),
        price=delivery_line_2.getPrice(),
        **invoice_movement_kw)

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

      self.portal.portal_deliveries.slapos_sale_invoice_builder.build(
          path=['%s/%%' % applied_rule_1.getPath(),
                '%s/%%' % applied_rule_2.getPath()])
      self.tic()

    self.checkSimulationMovement(invoice_movement_1)
    self.checkSimulationMovement(invoice_movement_1_bis)
    self.checkSimulationMovement(invoice_movement_2)

    invoice_line_1 = invoice_movement_1.getDeliveryValue()
    invoice_line_1_bis = invoice_movement_1_bis.getDeliveryValue()
    invoice_line_2 = invoice_movement_2.getDeliveryValue()
    self.assertNotEqual(invoice_line_1.getRelativeUrl(),
        invoice_line_2.getRelativeUrl())
    self.assertNotEqual(invoice_line_1, invoice_line_1_bis)
    self.assertEqual(invoice_line_1.getParentValue(),
        invoice_line_1_bis.getParentValue())

    line_kw = dict(line_portal_type='Invoice Line',
        cell_portal_type='Invoice Cell')
    self.checkDeliveryLine(invoice_movement_1, invoice_line_1, **line_kw)
    self.checkDeliveryLine(invoice_movement_1_bis, invoice_line_1_bis,
        **line_kw)
    self.checkDeliveryLine(invoice_movement_2, invoice_line_2, **line_kw)

    invoice_1 = invoice_line_1.getParentValue()
    invoice_2 = invoice_line_2.getParentValue()

    # The invoices are merged since they are from the same user.
    self.assertNotEqual(invoice_1.getRelativeUrl(),
        invoice_2.getRelativeUrl())


class TestSlapOSSaleInvoiceTransactionBuilder(TestSlapOSBuilderMixin):
  def checkSimulationMovement(self, simulation_movement):
    self.assertNotEqual(0.0, simulation_movement.getDeliveryRatio(), simulation_movement.getRelativeUrl())
    self.assertEqual(0.0, simulation_movement.getDeliveryError(), simulation_movement.getRelativeUrl())
    self.assertNotEqual(None, simulation_movement.getDeliveryValue(), simulation_movement.getRelativeUrl())

  def test_sale_invoice_transaction_builder(self):
    resource, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(is_accountable=True)
    project = instance_tree.getFollowUpValue()
    trade_condition = project.getSourceProjectRelatedValue(portal_type="Sale Trade Condition")
    currency = trade_condition.getPriceCurrencyValue()

    source = trade_condition.getSourceSectionValue()
    destination = instance_tree.getDestinationSectionValue()
    business_process = trade_condition.getSpecialiseValue()

    applied_rule_1 = self.portal.portal_simulation.newContent(
      portal_type='Applied Rule',
      specialise='portal_rules/slapos_delivery_root_simulation_rule'
    )
    applied_rule_2 = self.portal.portal_simulation.newContent(
      portal_type='Applied Rule',
      specialise='portal_rules/slapos_delivery_root_simulation_rule'
    )

    simulation_movement_1 = applied_rule_1.newContent(
        portal_type='Simulation Movement'
    )
    simulation_movement_2 = applied_rule_2.newContent(
        portal_type='Simulation Movement'
    )

    # linked invoice
    invoice_kw = dict(
      portal_type='Sale Invoice Transaction',
      source_value=source,
      source_section_value=source,
      price_currency_value=currency,
      resource_value=currency,
      specialise_value=trade_condition,
      created_by_builder=1,
      ledger='automated'
    )
    invoice_line_kw = dict(
      portal_type='Invoice Line',
      use='trade/sale',
      resource_value=resource,
      quantity_unit=resource.getQuantityUnit(),
      base_contribution=['base_amount/invoicing/discounted',
          'base_amount/invoicing/taxable'],
    )

    model_line_kw = dict(
      portal_type='Invoice Line',
      use='use/trade/tax',
      resource='service_module/slapos_tax',
      base_application='base_amount/invoicing/taxable'
    )
    invoice_1 = self.portal.accounting_module.newContent(
      start_date=DateTime('2012/01/01'),
      stop_date=DateTime('2012/02/01'),
      destination_value=destination,
      destination_section_value=destination,
      destination_decision_value=destination,
      destination_project_value=project,
      **invoice_kw
    )
    invoice_line_1 = invoice_1.newContent(
      price=1.2,
      quantity=3.4,
      **invoice_line_kw
    )
    invoice_line_1_tax = invoice_1.newContent(
      price=.196,
      quantity=invoice_line_1.getTotalPrice(),
      **model_line_kw
    )
    invoice_2 = self.portal.accounting_module.newContent(
      start_date=DateTime('2012/01/01'),
      stop_date=DateTime('2012/02/01'),
      destination_value=destination,
      destination_section_value=destination,
      destination_decision_value=destination,
      destination_project_value=project,
      **invoice_kw
    )
    invoice_line_2 = invoice_2.newContent(
      price=5.6,
      quantity=7.8,
      **invoice_line_kw
    )
    invoice_line_2_tax = invoice_2.newContent(
      price=.196,
      quantity=invoice_line_2.getTotalPrice(),
      **model_line_kw
    )
    self.portal.portal_workflow._jumpToStateFor(invoice_1, 'confirmed')
    self.portal.portal_workflow._jumpToStateFor(invoice_1, 'calculating')
    self.portal.portal_workflow._jumpToStateFor(invoice_2, 'confirmed')
    self.portal.portal_workflow._jumpToStateFor(invoice_2, 'calculating')

    # create new simulation movements
    invoice_movement_kw = dict(
        causality=[
            '%s/invoice' % business_process.getRelativeUrl(),
            '%s/invoice_path' % business_process.getRelativeUrl()
        ],
        trade_phase='slapos/invoicing',
        delivery_ratio=1.0,
        delivery_error=0.0,
        portal_type='Simulation Movement',
        base_contribution=['base_amount/invoicing/discounted',
            'base_amount/invoicing/taxable'],
        destination_value=destination,
        destination_section_value=destination,
        destination_decision_value=destination,
        destination_project_value=project,
        price_currency_value=currency,
        quantity_unit=resource.getQuantityUnit(),
        resource_value=resource,
        source_value=source,
        source_section_value=source,
        specialise_value=trade_condition,
        use='trade/sale',
        ledger='automated'
    )
    invoice_rule_1 = simulation_movement_1.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_1 = invoice_rule_1.newContent(
        start_date=invoice_1.getStartDate(),
        stop_date=invoice_1.getStopDate(),
        quantity=invoice_line_1.getQuantity(),
        price=invoice_line_1.getPrice(),
        delivery=invoice_line_1.getRelativeUrl(),
        **invoice_movement_kw)

    trade_movement_kw = dict(
        portal_type='Simulation Movement',
        price=.196,
        delivery_ratio=1.,
        delivery_error=0.,
        price_currency_value=currency,
        specialise_value=trade_condition,
        resource='service_module/slapos_tax',
        base_application='base_amount/invoicing/taxable',
        use='trade/tax',
        ledger='automated',
        causality=['%s/tax' % business_process.getRelativeUrl(),
            '%s/trade_model_path' % business_process.getRelativeUrl(),
            '%s/1' % trade_condition.getRelativeUrl()],
    )
    trade_model_rule_1 = invoice_movement_1.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_trade_model_simulation_rule'
    )
    trade_movement_1 = trade_model_rule_1.newContent(
        source=invoice_movement_1.getSource(),
        destination=invoice_movement_1.getDestination(),
        source_section=invoice_movement_1.getSourceSection(),
        destination_section=invoice_movement_1.getDestinationSection(),
        destination_project=invoice_movement_1.getDestinationProject(),
        quantity=invoice_movement_1.getTotalPrice(),
        delivery=invoice_line_1_tax.getRelativeUrl(),
        **trade_movement_kw
    )
    invoice_rule_2 = simulation_movement_2.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_2 = invoice_rule_2.newContent(
        start_date=invoice_2.getStartDate(),
        stop_date=invoice_2.getStopDate(),
        quantity=invoice_line_2.getQuantity(),
        price=invoice_line_2.getPrice(),
        delivery=invoice_line_2.getRelativeUrl(),
        **invoice_movement_kw)
    trade_model_rule_2 = invoice_movement_2.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_trade_model_simulation_rule'
    )
    trade_movement_2 = trade_model_rule_2.newContent(
        source=invoice_movement_2.getSource(),
        destination=invoice_movement_2.getDestination(),
        source_section=invoice_movement_2.getSourceSection(),
        destination_section=invoice_movement_2.getDestinationSection(),
        destination_project=invoice_movement_2.getDestinationProject(),
        quantity=invoice_movement_2.getTotalPrice(),
        delivery=invoice_line_2_tax.getRelativeUrl(),
        **trade_movement_kw
    )
    self.tic()

    invoice_1.updateCausalityState(solve_automatically=False)
    invoice_2.updateCausalityState(solve_automatically=False)
    self.tic()

    # test the test
    self.assertEqual('solved', invoice_1.getCausalityState())
    self.assertEqual('solved', invoice_2.getCausalityState())

    transaction_rule_1 = invoice_movement_1.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_transaction_simulation_rule'
    )
    transaction_movement_1_rec = transaction_rule_1.newContent(
      portal_type='Simulation Movement',
      causality=['%s/account' % business_process.getRelativeUrl(),
          '%s/account_debit_path' % business_process.getRelativeUrl()],
      destination=['account_module/payable'],
      destination_decision=invoice_movement_1.getDestinationDecision(),
      destination_section=invoice_movement_1.getDestinationSection(),
      destination_project=invoice_movement_1.getDestinationProject(),
      quantity_unit='unit/piece',
      resource_value=currency,
      source='account_module/receivable',
      source_section_value=source,
      specialise_value=trade_condition,
      trade_phase='slapos/accounting',
      ledger='automated',
      price=1.0,
      quantity=invoice_movement_1.getTotalPrice() * -1,
    )
    transaction_movement_1_rec_bis = transaction_movement_1_rec\
        .Base_createCloneDocument(batch_mode=1)
    transaction_movement_1_rec_bis.edit(delivery=None, delivery_ratio=1.0)
    transaction_movement_1_sal = transaction_rule_1.newContent(
      portal_type='Simulation Movement',
      causality=['%s/account' % business_process.getRelativeUrl(),
          '%s/account_credit_path' % business_process.getRelativeUrl()],
      destination=['account_module/purchase'],
      destination_decision=invoice_movement_1.getDestinationDecision(),
      destination_section=invoice_movement_1.getDestinationSection(),
      destination_project=invoice_movement_1.getDestinationProject(),
      quantity_unit='unit/piece',
      resource_value=currency,
      source='account_module/receivable',
      source_section_value=source,
      specialise_value=trade_condition,
      trade_phase='slapos/accounting',
      ledger='automated',
      price=1.0,
      quantity=invoice_movement_1.getTotalPrice(),
    )

    transation_model_rule_1 = trade_movement_1.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_transaction_simulation_rule'
    )
    transation_model_movement_1_rec = transation_model_rule_1.newContent(
      portal_type='Simulation Movement',
      causality=['%s/account' % business_process.getRelativeUrl(),
          '%s/accounting_tax2' % business_process.getRelativeUrl()],
      destination=['account_module/payable'],
      destination_decision=invoice_movement_1.getDestinationDecision(),
      destination_section=invoice_movement_1.getDestinationSection(),
      destination_project=invoice_movement_1.getDestinationProject(),
      quantity_unit='unit/piece',
      resource_value=currency,
      source='account_module/receivable',
      source_section_value=source,
      specialise_value=trade_condition,
      trade_phase='slapos/accounting',
      ledger='automated',
      price=1.0,
      quantity=trade_movement_1.getTotalPrice() * -1,
    )
    transation_model_movement_1_rec_bis = transation_model_movement_1_rec\
        .Base_createCloneDocument(batch_mode=1)
    transation_model_movement_1_rec_bis.edit(delivery=None, delivery_ratio=1.0)
    transation_model_movement_1_sal = transation_model_rule_1.newContent(
      portal_type='Simulation Movement',
      causality=['%s/account' % business_process.getRelativeUrl(),
          '%s/accounting_tax1' % business_process.getRelativeUrl()],
      destination=['account_module/refundable_vat'],
      destination_decision=invoice_movement_1.getDestinationDecision(),
      destination_section=invoice_movement_1.getDestinationSection(),
      destination_project=invoice_movement_1.getDestinationProject(),
      quantity_unit='unit/piece',
      resource_value=currency,
      source='account_module/coll_vat',
      source_section_value=source,
      specialise_value=trade_condition,
      trade_phase='slapos/accounting',
      ledger='automated',
      price=1.0,
      quantity=trade_movement_1.getTotalPrice(),
    )

    transaction_rule_2 = invoice_movement_2.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_transaction_simulation_rule'
    )
    transaction_movement_2_rec = transaction_rule_2.newContent(
      portal_type='Simulation Movement',
      causality=['%s/account' % business_process.getRelativeUrl(),
          '%s/account_debit_path' % business_process.getRelativeUrl()],
      destination=['account_module/payable'],
      destination_decision=invoice_movement_2.getDestinationDecision(),
      destination_section=invoice_movement_2.getDestinationSection(),
      destination_project=invoice_movement_2.getDestinationProject(),
      quantity_unit='unit/piece',
      resource_value=currency,
      source='account_module/receivable',
      source_section_value=source,
      specialise_value=trade_condition,
      trade_phase='slapos/accounting',
      ledger='automated',
      price=1.0,
      quantity=invoice_movement_2.getTotalPrice() * -1,
    )
    transaction_movement_2_sal = transaction_rule_2.newContent(
      portal_type='Simulation Movement',
      causality=['%s/account' % business_process.getRelativeUrl(),
          '%s/account_credit_path' % business_process.getRelativeUrl()],
      destination=['account_module/purchase'],
      destination_decision=invoice_movement_2.getDestinationDecision(),
      destination_section=invoice_movement_2.getDestinationSection(),
      destination_project=invoice_movement_2.getDestinationProject(),
      quantity_unit='unit/piece',
      resource_value=currency,
      source='account_module/receivable',
      source_section_value=source,
      specialise_value=trade_condition,
      trade_phase='slapos/accounting',
      ledger='automated',
      price=1.0,
      quantity=invoice_movement_2.getTotalPrice(),
    )

    transation_model_rule_2 = trade_movement_2.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_transaction_simulation_rule'
    )
    transation_model_movement_2_rec = transation_model_rule_2.newContent(
      portal_type='Simulation Movement',
      causality=['%s/account' % business_process.getRelativeUrl(),
          '%s/accounting_tax2' % business_process.getRelativeUrl()],
      destination=['account_module/payable'],
      destination_decision=invoice_movement_2.getDestinationDecision(),
      destination_section=invoice_movement_2.getDestinationSection(),
      destination_project=invoice_movement_2.getDestinationProject(),
      quantity_unit='unit/piece',
      resource_value=currency,
      source='account_module/receivable',
      source_section_value=source,
      specialise_value=trade_condition,
      trade_phase='slapos/accounting',
      ledger='automated',
      price=1.0,
      quantity=trade_movement_2.getTotalPrice() * -1,
    )
    transation_model_movement_2_sal = transation_model_rule_2.newContent(
      portal_type='Simulation Movement',
      causality=['%s/account' % business_process.getRelativeUrl(),
          '%s/accounting_tax1' % business_process.getRelativeUrl()],
      destination=['account_module/refundable_vat'],
      destination_decision=invoice_movement_2.getDestinationDecision(),
      destination_section=invoice_movement_2.getDestinationSection(),
      destination_project=invoice_movement_2.getDestinationProject(),
      quantity_unit='unit/piece',
      resource_value=currency,
      source='account_module/coll_vat',
      source_section_value=source,
      specialise_value=trade_condition,
      trade_phase='slapos/accounting',
      ledger='automated',
      price=1.0,
      quantity=trade_movement_2.getTotalPrice(),
    )

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

      self.portal.portal_deliveries.slapos_sale_invoice_transaction_builder.build(
          path='%s/%%' % applied_rule_1.getPath())
      self.portal.portal_deliveries.slapos_sale_invoice_transaction_builder.build(
          path='%s/%%' % applied_rule_2.getPath())
      self.tic()

    self.checkSimulationMovement(transaction_movement_1_rec)
    self.checkSimulationMovement(transaction_movement_1_rec_bis)
    self.checkSimulationMovement(transaction_movement_1_sal)
    self.checkSimulationMovement(transaction_movement_2_rec)
    self.checkSimulationMovement(transaction_movement_2_sal)

    self.checkSimulationMovement(transation_model_movement_1_rec)
    self.checkSimulationMovement(transation_model_movement_1_rec_bis)
    self.checkSimulationMovement(transation_model_movement_1_sal)
    self.checkSimulationMovement(transation_model_movement_2_rec)
    self.checkSimulationMovement(transation_model_movement_2_sal)

    transaction_line_1_rec = transaction_movement_1_rec.getDeliveryValue()
    transaction_line_1_rec_bis = transaction_movement_1_rec_bis.getDeliveryValue()
    transaction_line_1_sal = transaction_movement_1_sal.getDeliveryValue()
    transaction_line_2_rec = transaction_movement_2_rec.getDeliveryValue()
    transaction_line_2_sal = transaction_movement_2_sal.getDeliveryValue()

    transation_model_line_1_rec = transation_model_movement_1_rec.getDeliveryValue()
    transation_model_line_1_rec_bis = transation_model_movement_1_rec_bis.getDeliveryValue()
    transation_model_line_1_sal = transation_model_movement_1_sal.getDeliveryValue()
    transation_model_line_2_rec = transation_model_movement_2_rec.getDeliveryValue()
    transation_model_line_2_sal = transation_model_movement_2_sal.getDeliveryValue()

    def checkTransactionLine(simulation_movement, transaction_line,
          category_list):
      self.assertEqual('Sale Invoice Transaction Line',
          transaction_line.getPortalType())
      self.assertSameSet([
          'resource/%s' % currency.getRelativeUrl()] + category_list,
        transaction_line.getCategoryList()
      )
      self.assertTrue(
        abs(simulation_movement.getQuantity() - transaction_line.getQuantity()
          * simulation_movement.getDeliveryRatio()) <= 0.000000000000001)
      self.assertEqual(simulation_movement.getPrice(),
          transaction_line.getPrice())
      self.assertFalse(transaction_line.hasStartDate())
      self.assertFalse(transaction_line.hasStopDate())
      self.assertEqual([], transaction_line.contentValues(
          portal_type='Delivery Cell'))
      self.assertIn(simulation_movement.getRelativeUrl(),
          transaction_line.getDeliveryRelatedList(
              portal_type='Simulation Movement'))

    checkTransactionLine(transaction_movement_1_rec, transaction_line_1_rec,
        ['source/account_module/receivable',
            'destination/account_module/payable'])
    checkTransactionLine(transaction_movement_1_rec_bis,
        transaction_line_1_rec_bis,
        ['source/account_module/receivable',
            'destination/account_module/payable'])
    checkTransactionLine(transaction_movement_1_sal, transaction_line_1_sal,
        ['destination/account_module/purchase',
            'source/account_module/receivable'])
    checkTransactionLine(transaction_movement_2_rec, transaction_line_2_rec,
        ['source/account_module/receivable',
            'destination/account_module/payable'])
    checkTransactionLine(transaction_movement_2_sal, transaction_line_2_sal,
        ['destination/account_module/purchase',
            'source/account_module/receivable'])

    checkTransactionLine(transation_model_movement_1_rec, transation_model_line_1_rec,
        ['source/account_module/receivable',
            'destination/account_module/payable'])
    checkTransactionLine(transation_model_movement_1_rec_bis,
        transation_model_line_1_rec_bis,
        ['source/account_module/receivable',
            'destination/account_module/payable'])
    checkTransactionLine(transation_model_movement_1_sal, transation_model_line_1_sal,
        ['destination/account_module/refundable_vat',
            'source/account_module/coll_vat'])
    checkTransactionLine(transation_model_movement_2_rec, transation_model_line_2_rec,
        ['source/account_module/receivable',
            'destination/account_module/payable'])
    checkTransactionLine(transation_model_movement_2_sal, transation_model_line_2_sal,
        ['destination/account_module/refundable_vat',
            'source/account_module/coll_vat'])

    self.assertEqual(invoice_1.getRelativeUrl(),
        transaction_line_1_rec.getParentValue().getRelativeUrl())
    self.assertEqual(invoice_1.getRelativeUrl(),
        transaction_line_1_rec_bis.getParentValue().getRelativeUrl())
    self.assertEqual(invoice_1.getRelativeUrl(),
        transaction_line_1_sal.getParentValue().getRelativeUrl())
    self.assertEqual(invoice_2.getRelativeUrl(),
        transaction_line_2_rec.getParentValue().getRelativeUrl())
    self.assertEqual(invoice_2.getRelativeUrl(),
        transaction_line_2_sal.getParentValue().getRelativeUrl())

    self.assertEqual(invoice_1.getRelativeUrl(),
        transation_model_line_1_rec.getParentValue().getRelativeUrl())
    self.assertEqual(invoice_1.getRelativeUrl(),
        transation_model_line_1_rec_bis.getParentValue().getRelativeUrl())
    self.assertEqual(invoice_1.getRelativeUrl(),
        transation_model_line_1_sal.getParentValue().getRelativeUrl())
    self.assertEqual(invoice_2.getRelativeUrl(),
        transation_model_line_2_rec.getParentValue().getRelativeUrl())
    self.assertEqual(invoice_2.getRelativeUrl(),
        transation_model_line_2_sal.getParentValue().getRelativeUrl())

    def checkTransactionedInvoice(invoice):
      self.assertEqual('confirmed', invoice.getSimulationState())
      self.assertEqual('building', invoice.getCausalityState())
      invoice.updateCausalityState(solve_automatically=False)
      self.assertEqual('solved', invoice.getCausalityState())

    checkTransactionedInvoice(invoice_1)
    checkTransactionedInvoice(invoice_2)

    transaction_movement_1_rec_bis2 = transaction_movement_1_rec\
        .Base_createCloneDocument(batch_mode=1)
    transaction_movement_1_rec_bis2.edit(delivery=None, delivery_ratio=1.0)
    transation_model_movement_1_rec_bis2 = transation_model_movement_1_rec\
        .Base_createCloneDocument(batch_mode=1)
    transation_model_movement_1_rec_bis2.edit(delivery=None, delivery_ratio=1.0)
    self.tic()
    self.portal.portal_deliveries.slapos_sale_invoice_transaction_builder.build(
        path='%s/%%' % applied_rule_1.getPath())
    self.portal.portal_deliveries.slapos_sale_invoice_transaction_builder.build(
        path='%s/%%' % applied_rule_2.getPath())
    self.tic()

    # as invoice_1 has been updated it is time to update its causality
    # with automatic solving
    invoice_1.updateCausalityState(solve_automatically=True)
    self.tic()

    self.checkSimulationMovement(transaction_movement_1_rec_bis2)
    transaction_line_1_rec_bis2 = transaction_movement_1_rec_bis2\
        .getDeliveryValue()
    checkTransactionLine(transaction_movement_1_rec_bis2,
        transaction_line_1_rec_bis2,
        ['source/account_module/receivable',
            'destination/account_module/payable'])
    self.assertEqual(invoice_1.getRelativeUrl(),
        transaction_line_1_rec_bis2.getParentValue().getRelativeUrl())

    self.checkSimulationMovement(transation_model_movement_1_rec_bis2)
    transation_model_line_1_rec_bis2 = transation_model_movement_1_rec_bis2\
        .getDeliveryValue()
    checkTransactionLine(transation_model_movement_1_rec_bis2,
        transation_model_line_1_rec_bis2,
        ['source/account_module/receivable',
            'destination/account_module/payable'])
    self.assertEqual(invoice_1.getRelativeUrl(),
        transation_model_line_1_rec_bis2.getParentValue().getRelativeUrl())

    self.assertEqual('solved', invoice_1.getCausalityState())
    self.assertEqual('confirmed', invoice_1.getSimulationState())
    self.assertEqual('solved', invoice_2.getCausalityState())
    self.assertEqual('confirmed', invoice_2.getSimulationState())

class TestSlapOSSaleInvoiceTransactionTradeModelBuilder(TestSlapOSBuilderMixin):
  def checkSimulationMovement(self, simulation_movement):
    self.assertNotEqual(0.0, simulation_movement.getDeliveryRatio())
    self.assertEqual(0.0, simulation_movement.getDeliveryError())
    self.assertNotEqual(None, simulation_movement.getDeliveryValue())

  def test_sale_invoice_transaction_trade_model_builder(self):
    resource, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(is_accountable=True)
    project = instance_tree.getFollowUpValue()
    trade_condition = project.getSourceProjectRelatedValue(portal_type="Sale Trade Condition")
    currency = trade_condition.getPriceCurrencyValue()
    source = trade_condition.getSourceSectionValue()
    destination = instance_tree.getDestinationSectionValue()
    business_process = trade_condition.getSpecialiseValue()

    applied_rule_1 = self.portal.portal_simulation.newContent(
      portal_type='Applied Rule',
      specialise='portal_rules/slapos_delivery_root_simulation_rule'
    )
    applied_rule_2 = self.portal.portal_simulation.newContent(
      portal_type='Applied Rule',
      specialise='portal_rules/slapos_delivery_root_simulation_rule'
    )

    simulation_movement_1 = applied_rule_1.newContent(
        portal_type='Simulation Movement'
    )
    simulation_movement_2 = applied_rule_2.newContent(
        portal_type='Simulation Movement'
    )

    # linked invoice
    invoice_kw = dict(
      portal_type='Sale Invoice Transaction',
      source_value=source,
      source_section_value=source,
      price_currency_value=currency,
      resource_value=currency,
      specialise_value=trade_condition,
      ledger='automated',
      created_by_builder=1
    )
    invoice_line_kw = dict(
      portal_type='Invoice Line',
      use='trade/sale',
      ledger='automated',
      resource_value=resource,
      quantity_unit=resource.getQuantityUnit(),
      base_contribution=['base_amount/invoicing/discounted',
          'base_amount/invoicing/taxable'],
    )

    invoice_1 = self.portal.accounting_module.newContent(
      start_date=DateTime('2012/01/01'),
      stop_date=DateTime('2012/02/01'),
      destination_value=destination,
      destination_section_value=destination,
      destination_decision_value=destination,
      destination_project_value=project,
      **invoice_kw
    )
    invoice_line_1 = invoice_1.newContent(
      price=1.2,
      quantity=3.4,
      **invoice_line_kw
    )
    invoice_2 = self.portal.accounting_module.newContent(
      start_date=DateTime('2012/01/01'),
      stop_date=DateTime('2012/02/01'),
      destination_value=destination,
      destination_section_value=destination,
      destination_decision_value=destination,
      destination_project_value=project,
      **invoice_kw
    )
    invoice_line_2 = invoice_2.newContent(
      price=5.6,
      quantity=7.8,
      **invoice_line_kw
    )
    self.portal.portal_workflow._jumpToStateFor(invoice_1, 'confirmed')
    self.portal.portal_workflow._jumpToStateFor(invoice_1, 'calculating')
    self.portal.portal_workflow._jumpToStateFor(invoice_2, 'confirmed')
    self.portal.portal_workflow._jumpToStateFor(invoice_2, 'calculating')

    # create new simulation movements
    invoice_movement_kw = dict(
        causality=[
            '%s/invoice' % business_process.getRelativeUrl(),
            '%s/invoice_path' % business_process.getRelativeUrl()
        ],
        trade_phase='slapos/invoicing',
        delivery_ratio=1.0,
        delivery_error=0.0,
        portal_type='Simulation Movement',
        base_contribution=['base_amount/invoicing/discounted',
            'base_amount/invoicing/taxable'],
        destination_value=destination,
        destination_decision_value=destination,
        destination_section_value=destination,
        destination_project_value=project,
        price_currency_value=currency,
        quantity_unit='unit/piece',
        resource_value=resource,
        source_value=source,
        source_section_value=source,
        specialise_value=trade_condition,
        ledger='automated',
        use='trade/sale',
    )
    invoice_rule_1 = simulation_movement_1.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_1 = invoice_rule_1.newContent(
        start_date=invoice_1.getStartDate(),
        stop_date=invoice_1.getStopDate(),
        quantity=invoice_line_1.getQuantity(),
        price=invoice_line_1.getPrice(),
        delivery_value=invoice_line_1,
        **invoice_movement_kw)

    invoice_rule_2 = simulation_movement_2.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_invoice_simulation_rule')
    invoice_movement_2 = invoice_rule_2.newContent(
        start_date=invoice_2.getStartDate(),
        stop_date=invoice_2.getStopDate(),
        quantity=invoice_line_2.getQuantity(),
        price=invoice_line_2.getPrice(),
        delivery_value=invoice_line_2,
        **invoice_movement_kw)

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

    invoice_1.updateCausalityState(solve_automatically=False)
    invoice_2.updateCausalityState(solve_automatically=False)
    self.tic()

    # test the test
    self.assertEqual('solved', invoice_1.getCausalityState())
    self.assertEqual('solved', invoice_2.getCausalityState())

    model_movement_kw = dict(
      base_application='base_amount/invoicing/taxable',
      ledger='automated',
      price_currency_value=currency,
      quantity_unit='unit/piece',
      source_value=source,
      source_section_value=source,
      specialise_value=trade_condition,
      portal_type='Simulation Movement',
    )
    model_rule_1 = invoice_movement_1.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_trade_model_simulation_rule'
    )
    model_movement_1_tax = model_rule_1.newContent(
      destination=invoice_movement_1.getDestination(),
      destination_section=invoice_movement_1.getDestinationSection(),
      destination_decision=invoice_movement_1.getDestinationDecision(),
      destination_project=invoice_movement_1.getDestinationProject(),
      resource='service_module/slapos_tax',
      trade_phase='slapos/tax',
      causality=['%s/tax' % business_process.getRelativeUrl(),
          '%s/trade_model_path' % business_process.getRelativeUrl(),
          '%s/1' % trade_condition.getRelativeUrl(),
      ],
      price=.196,
      quantity=invoice_movement_1.getTotalPrice(),
      **model_movement_kw
    )
    model_movement_1_tax_2 = model_rule_1.newContent(
      destination=invoice_movement_1.getDestination(),
      destination_section=invoice_movement_1.getDestinationSection(),
      destination_decision=invoice_movement_1.getDestinationDecision(),
      destination_project=invoice_movement_1.getDestinationProject(),
      resource='service_module/slapos_tax',
      trade_phase='slapos/tax',
      causality=['%s/tax' % business_process.getRelativeUrl(),
          '%s/trade_model_path' % business_process.getRelativeUrl(),
          '%s/1' % trade_condition.getRelativeUrl(),
      ],
      price=.196,
      quantity=.0,
      **model_movement_kw
    )

    model_rule_2 = invoice_movement_2.newContent(
        portal_type='Applied Rule',
        specialise='portal_rules/slapos_trade_model_simulation_rule'
    )
    model_movement_2_tax = model_rule_2.newContent(
      destination=invoice_movement_2.getDestination(),
      destination_section=invoice_movement_2.getDestinationSection(),
      destination_decision=invoice_movement_2.getDestinationDecision(),
      destination_project=invoice_movement_2.getDestinationProject(),
      resource='service_module/slapos_tax',
      trade_phase='slapos/tax',
      causality=['%s/tax' % business_process.getRelativeUrl(),
          '%s/trade_model_path' % business_process.getRelativeUrl(),
          '%s/1' % trade_condition.getRelativeUrl(),
      ],
      price=.196,
      quantity=invoice_movement_2.getTotalPrice(),
      **model_movement_kw
    )

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

      self.portal.portal_deliveries\
          .slapos_sale_invoice_transaction_trade_model_builder.build(
          path='%s/%%' % applied_rule_1.getPath())
      self.portal.portal_deliveries\
          .slapos_sale_invoice_transaction_trade_model_builder.build(
          path='%s/%%' % applied_rule_2.getPath())
      self.tic()

    self.checkSimulationMovement(model_movement_1_tax)
    self.assertEqual(0.0, model_movement_1_tax_2.getDeliveryRatio())
    self.assertEqual(0.0, model_movement_1_tax_2.getDeliveryError())
    self.assertNotEqual(None, model_movement_1_tax_2.getDeliveryValue())
    self.checkSimulationMovement(model_movement_2_tax)

    model_line_1_tax = model_movement_1_tax.getDeliveryValue()
    model_line_1_tax_2 = model_movement_1_tax_2.getDeliveryValue()
    self.assertEqual(model_line_1_tax, model_line_1_tax_2)
    model_line_2_tax = model_movement_2_tax.getDeliveryValue()

    def checkModelLine(simulation_movement, transaction_line, category_list):
      self.assertEqual('Invoice Line',
          transaction_line.getPortalType())
      self.assertSameSet([
          'quantity_unit/unit/piece'
          ] + category_list,
        transaction_line.getCategoryList()
      )
      self.assertEqual(simulation_movement.getQuantity(),
          transaction_line.getQuantity()
          * simulation_movement.getDeliveryRatio())
      self.assertEqual(simulation_movement.getPrice(),
          transaction_line.getPrice())
      self.assertFalse(transaction_line.hasStartDate())
      self.assertFalse(transaction_line.hasStopDate())
      self.assertEqual([], transaction_line.contentValues(
          portal_type='Delivery Cell'))
      self.assertIn(simulation_movement.getRelativeUrl(),
          transaction_line.getDeliveryRelatedList(
              portal_type='Simulation Movement'))

    checkModelLine(model_movement_1_tax, model_line_1_tax, [
        'base_application/base_amount/invoicing/taxable',
        'resource/service_module/slapos_tax',
         'use/trade/tax'])
    checkModelLine(model_movement_2_tax, model_line_2_tax, [
        'base_application/base_amount/invoicing/taxable',
        'resource/service_module/slapos_tax',
         'use/trade/tax'])

    self.assertEqual(invoice_1.getRelativeUrl(),
        model_line_1_tax.getParentValue().getRelativeUrl())
    self.assertEqual(invoice_2.getRelativeUrl(),
        model_line_2_tax.getParentValue().getRelativeUrl())

    def checkModeledInvoice(invoice):
      self.assertEqual('confirmed', invoice.getSimulationState())
      self.assertEqual('building', invoice.getCausalityState())
      invoice.updateCausalityState(solve_automatically=False)
      self.assertEqual('solved', invoice.getCausalityState())

    checkModeledInvoice(invoice_1)
    checkModeledInvoice(invoice_2)

    model_movement_1_tax_bis = model_movement_1_tax.Base_createCloneDocument(
        batch_mode=1)
    model_movement_1_tax_bis.edit(delivery=None, delivery_ratio=1.0)
    self.tic()
    self.portal.portal_deliveries\
        .slapos_sale_invoice_transaction_trade_model_builder.build(
        path='%s/%%' % applied_rule_1.getPath())
    self.portal.portal_deliveries\
        .slapos_sale_invoice_transaction_trade_model_builder.build(
        path='%s/%%' % applied_rule_2.getPath())
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

      # as invoice_1 has been updated it is time to update its causality
      # with automatic solving
      invoice_1.updateCausalityState(solve_automatically=True)
      self.tic()

    self.checkSimulationMovement(model_movement_1_tax_bis)

    model_line_1_tax_bis = model_movement_1_tax_bis.getDeliveryValue()
    checkModelLine(model_movement_1_tax_bis, model_line_1_tax_bis, [
        'base_application/base_amount/invoicing/taxable',
        'resource/service_module/slapos_tax',
         'use/trade/tax'])
    self.assertEqual(invoice_1.getRelativeUrl(),
        model_line_1_tax_bis.getParentValue().getRelativeUrl())

    model_movement_2_tax_bis = model_movement_2_tax.Base_createCloneDocument(
        batch_mode=1)
    model_movement_2_tax_bis.edit(delivery=None, delivery_ratio=1.0,
        quantity=.0)

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
      self.portal.portal_deliveries\
          .slapos_sale_invoice_transaction_trade_model_builder.build(
          path='%s/%%' % applied_rule_1.getPath())
      self.portal.portal_deliveries\
          .slapos_sale_invoice_transaction_trade_model_builder.build(
          path='%s/%%' % applied_rule_2.getPath())
      self.tic()

      # as invoice_2 has been updated it is time to update its causality
      # with automatic solving
      invoice_2.updateCausalityState(solve_automatically=True)
      self.tic()

    self.assertEqual(0.0, model_movement_2_tax_bis.getDeliveryRatio())
    self.assertEqual(0.0, model_movement_2_tax_bis.getDeliveryError())
    self.assertNotEqual(None, model_movement_2_tax_bis.getDeliveryValue())
    model_line_2_tax_bis = model_movement_2_tax_bis.getDeliveryValue()
    checkModelLine(model_movement_2_tax_bis, model_line_2_tax_bis, [
        'base_application/base_amount/invoicing/taxable',
        'resource/service_module/slapos_tax',
         'use/trade/tax'])
    self.assertEqual(invoice_2.getRelativeUrl(),
        model_line_2_tax_bis.getParentValue().getRelativeUrl())

"""
class TestSlapOSAggregatedDeliveryBuilder(SlapOSTestCaseMixin):
  def emptyBuild(self, **kw):
    delivery_list = self._build(**kw)
    self.assertSameSet([], delivery_list)
    return delivery_list

  def fullBuild(self, **kw):
    delivery_list = self._build(**kw)
    self.assertNotEqual([], delivery_list)
    return delivery_list

  def _build(self, **kw):
    return self.portal.portal_orders.slapos_aggregated_delivery_builder.build(
        **kw)

  def _createDelivery(self, **kwargs):
    delivery = self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredInstanceDeliveryTemplate()
        ).Base_createCloneDocument(batch_mode=1)
    delivery.edit(**kwargs)
    self.portal.portal_workflow._jumpToStateFor(delivery, 'delivered')
    return delivery

  def _addDeliveryLine(self, delivery, **kwargs):
    kwargs.setdefault('portal_type', 'Sale Packing List Line')
    kwargs.setdefault('quantity', 1.0)
    kwargs.setdefault('resource', 'service_module/slapos_instance_setup')
    kwargs.setdefault('price', 0.0)
    delivery_line = delivery.newContent(**kwargs)
    return delivery_line

  def test(self):
    person = self.portal.person_module\
        .newContent(portal_type="Person")
    delivery = self._createDelivery(destination_value=person,
        destination_decision_value=person)
    delivery_line = self._addDeliveryLine(delivery)
    self.tic()

    delivery_list = self.fullBuild(uid=delivery_line.getUid())

    self.assertEqual(1, len(delivery_list))

    built_delivery = delivery_list[0]

    self.assertEqual(delivery_line.getGroupingReference(),
        built_delivery.getReference())
    self.assertEqual('confirmed', built_delivery.getSimulationState())
    self.assertEqual('building', built_delivery.getCausalityState())
    self.assertSameSet([
        'ledger/automated',
        'destination/%s' % person.getRelativeUrl(),
        'destination_decision/%s' % person.getRelativeUrl(),
        'destination_section/%s' % person.getRelativeUrl(),
        'destination_project/%s' % self.slapos_project.getRelativeUrl(),
        'price_currency/currency_module/EUR',
        'source/%s' % self.expected_slapos_organisation,
        'source_section/%s' % self.expected_slapos_organisation,
        'specialise/%s' % self.slapos_trade_condition.getRelativeUrl()],
        built_delivery.getCategoryList())
    self.assertEqual(DateTime().earliestTime(), built_delivery.getStartDate())
    delivery_line_list = built_delivery.contentValues(
        portal_type='Sale Packing List Line')
    self.assertEqual(1, len(delivery_line_list))
    built_delivery_line = delivery_line_list[0]
    self.assertEqual(1.0, built_delivery_line.getQuantity())
    self.assertEqual(0.0, built_delivery_line.getPrice())
    self.assertEqual(delivery_line.getResource(),
        built_delivery_line.getResource())

  def test_many_lines(self):
    person = self.portal.person_module\
        .newContent(portal_type="Person")
    delivery = self._createDelivery(destination_value=person,
        destination_decision_value=person)
    setup_line_1 = self._addDeliveryLine(delivery)
    setup_line_2 = self._addDeliveryLine(delivery)
    cleanup_line = self._addDeliveryLine(delivery,
        resource='service_module/slapos_instance_cleanup')
    update_line = self._addDeliveryLine(delivery,
        resource='service_module/slapos_instance_update')
    subscription_line = self._addDeliveryLine(delivery,
        resource='service_module/slapos_instance_subscription')
    self.tic()

    delivery_list = self.fullBuild(uid=[setup_line_1.getUid(),
        setup_line_2.getUid(), cleanup_line.getUid(), update_line.getUid(),
        subscription_line.getUid()])

    self.assertEqual(1, len(delivery_list))

    built_delivery = delivery_list[0]

    self.assertEqual(setup_line_1.getGroupingReference(),
        built_delivery.getReference())
    self.assertEqual(setup_line_2.getGroupingReference(),
        built_delivery.getReference())
    self.assertEqual(cleanup_line.getGroupingReference(),
        built_delivery.getReference())
    self.assertEqual(update_line.getGroupingReference(),
        built_delivery.getReference())

    self.assertEqual('confirmed', built_delivery.getSimulationState())
    self.assertEqual('building', built_delivery.getCausalityState())
    delivery_line_list = built_delivery.contentValues(
        portal_type='Sale Packing List Line')
    self.assertEqual(4, len(delivery_line_list))

    built_setup_line = [q for q in delivery_line_list if q.getResource() == 'service_module/slapos_instance_setup'][0]
    built_cleanup_line = [q for q in delivery_line_list if q.getResource() == 'service_module/slapos_instance_cleanup'][0]
    built_update_line = [q for q in delivery_line_list if q.getResource() == 'service_module/slapos_instance_update'][0]
    built_subscription_line = [q for q in delivery_line_list if q.getResource() == 'service_module/slapos_instance_subscription'][0]

    self.assertEqual(2.0, built_setup_line.getQuantity())
    self.assertEqual(0.0, built_setup_line.getPrice())
    self.assertEqual(setup_line_1.getResource(),
        built_setup_line.getResource())

    self.assertEqual(1.0, built_cleanup_line.getQuantity())
    self.assertEqual(0.0, built_cleanup_line.getPrice())
    self.assertEqual(cleanup_line.getResource(),
        built_cleanup_line.getResource())

    self.assertEqual(1.0, built_update_line.getQuantity())
    self.assertEqual(0.0, built_update_line.getPrice())
    self.assertEqual(update_line.getResource(),
        built_update_line.getResource())

    self.assertEqual(1.0, built_subscription_line.getQuantity())
    self.assertAlmostEqual(0.0, built_subscription_line.getPrice(), 3)
    self.assertEqual(subscription_line.getResource(),
        built_subscription_line.getResource())

  def test_added_after(self):
    person = self.portal.person_module\
        .newContent(portal_type="Person")
    delivery = self._createDelivery(destination_value=person,
        destination_decision_value=person)
    delivery_line = self._addDeliveryLine(delivery)
    self.tic()

    delivery_list = self.fullBuild(uid=delivery_line.getUid())

    self.assertEqual(1, len(delivery_list))

    built_delivery = delivery_list[0]

    self.assertEqual(delivery_line.getGroupingReference(),
        built_delivery.getReference())
    self.assertEqual('confirmed', built_delivery.getSimulationState())
    self.assertEqual('building', built_delivery.getCausalityState())
    delivery_line_list = built_delivery.contentValues(
        portal_type='Sale Packing List Line')
    self.assertEqual(1, len(delivery_line_list))
    built_delivery_line = delivery_line_list[0]
    self.assertEqual(1.0, built_delivery_line.getQuantity())
    self.assertEqual(0.0, built_delivery_line.getPrice())
    self.assertEqual(delivery_line.getResource(),
        built_delivery_line.getResource())

    delivery_line_2 = self._addDeliveryLine(delivery)
    self.tic()

    delivery_list = self.fullBuild(uid=delivery_line_2.getUid())

    self.assertEqual(1, len(delivery_list))

    new_built_delivery = delivery_list[0]
    self.assertEqual(built_delivery, new_built_delivery)

    self.assertEqual(delivery_line_2.getGroupingReference(),
        built_delivery.getReference())
    self.assertEqual('confirmed', built_delivery.getSimulationState())
    self.assertEqual('building', built_delivery.getCausalityState())
    delivery_line_list = built_delivery.contentValues(
        portal_type='Sale Packing List Line')
    self.assertEqual(1, len(delivery_line_list))
    built_delivery_line = delivery_line_list[0]
    self.assertEqual(2.0, built_delivery_line.getQuantity())
    self.assertEqual(0.0, built_delivery_line.getPrice())
    self.assertEqual(delivery_line_2.getResource(),
        built_delivery_line.getResource())
"""