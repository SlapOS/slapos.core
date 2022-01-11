# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName


class TestSlapOSSaleSupply(SlapOSTestCaseMixin):

  def test_check(self):
    # Create 2 projects
    project_1 = self.portal.project_module.newContent(
      portal_type="Project",
      title="project_1"
    )
    project_2 = self.portal.project_module.newContent(
      portal_type="Project",
      title="project_2"
    )
    # Create 2 software product
    # - one with 1 release and 1 type
    # - one with 2 releases and 2 types
    simple_product = self.portal.software_product_module.newContent(
      portal_type="Software Product",
      title="Simple Product",
    )
    simple_product.newContent(
      portal_type="Software Product Type Variation",
      title="software_type_a"
    )
    simple_product.newContent(
      portal_type="Software Product Release Variation",
      url_string="http://example.org/release_1"
    )

    complex_product = self.portal.software_product_module.newContent(
      portal_type="Software Product",
      title="Complex Product"
    )
    complex_product.newContent(
      portal_type="Software Product Type Variation",
      title="software_type_b"
    )
    complex_product.newContent(
      portal_type="Software Product Type Variation",
      title="software_type_c"
    )
    complex_product.newContent(
      portal_type="Software Product Release Variation",
      url_string="http://example.org/release_2"
    )
    complex_product.newContent(
      portal_type="Software Product Release Variation",
      url_string="http://example.org/release_3"
    )

    # create 2 users
    person_1 = self.portal.person_module.newContent()
    person_2 = self.portal.person_module.newContent()

    # Create 2 sale supplies
    # - one for everybody (no destination)
    # - one for one specific user
    now = DateTime()
    wrong_currency_supply = self.portal.sale_supply_module.newContent(
      title="Wrong currency Supply",
      start_date_range_min=now,
      destination_project_value=project_1,
      price_currency="currency_module/CNY",
    )
    everybody_supply = self.portal.sale_supply_module.newContent(
      title="Everybody Supply",
      start_date_range_min=now,
      destination_project_value=project_1,
      price_currency="currency_module/EUR",
    )
    person_1_supply = self.portal.sale_supply_module.newContent(
      title="Person 1 Supply",
      start_date_range_min=now,
      destination_project_value=project_1,
      destination_value=person_1,
      price_currency="currency_module/EUR"
    )

    # Create sale Line/Cell for all product combination
    sale_supply_cell_list = []
    sale_supply_line_list = []
    base_id = 'path'
    base_price = 0
    for sale_supply in [wrong_currency_supply, everybody_supply, person_1_supply]:

      base_price += 1
      sale_supply_line = sale_supply.newContent(
        title="without resource",
        portal_type="Sale Supply Line",
        base_price=base_price,
      )
      sale_supply_line_list.append(sale_supply_line)

      for software_product in [simple_product, complex_product]:
        sale_supply_line = sale_supply.newContent(
          title="%s without price" % software_product.getTitle(),
          portal_type="Sale Supply Line",
          resource_value=software_product,
          quantity_unit=software_product.getQuantityUnit(),
        )
        sale_supply_line_list.append(sale_supply_line)

        base_price += 1
        sale_supply_line = sale_supply.newContent(
          title="%s without variation" % software_product.getTitle(),
          portal_type="Sale Supply Line",
          resource_value=software_product,
          base_price=base_price,
          quantity_unit=software_product.getQuantityUnit(),
        )
        sale_supply_line_list.append(sale_supply_line)

        sale_supply_line = sale_supply.newContent(
          title="%s with variation" % software_product.getTitle(),
          portal_type="Sale Supply Line",
          resource_value=software_product,
          quantity_unit=software_product.getQuantityUnit(),
        )
        sale_supply_line_list.append(sale_supply_line)
        base_price += 1
        sale_supply_line.edit(
          base_price=base_price,
          p_variation_base_category_list=sale_supply_line.getVariationRangeBaseCategoryList()
        )
        sale_supply_line.setCellRange(
          base_id=base_id,
          *sale_supply_line.SupplyLine_asCellRange(base_id=base_id)
        )
        for cell_key in list(sale_supply_line.getCellKeyList(base_id=base_id)):
          sale_supply_cell = sale_supply_line.newCell(
            base_id=base_id,
            portal_type='Sale Supply Cell',
            *cell_key
          )
          base_price += 1
          sale_supply_cell.edit(
            mapped_value_property_list=['base_price'],
            base_price=base_price,
            predicate_category_list=cell_key,
            variation_category_list=cell_key
          )
          sale_supply_cell_list.append(sale_supply_cell)
      sale_supply.validate()

    self.tic()
    # Create movements
    # one for everybody
    # one for one specific user
    # check if predicates match
    i = 0
    domain_tool = getToolByName(self.portal, 'portal_domains')
    for software_product in [simple_product, complex_product]:
      for software_type in software_product.contentValues(portal_type="Software Product Type Variation"):
        for software_release in software_product.contentValues(portal_type="Software Product Release Variation"):
          for project in [project_1, project_2, None]:
            for destination in [person_1, person_2, None]:
              for start_date in [now, now-1, None]:

                tmp_context = self.portal.portal_trash.newContent(
                  portal_type='Movement',
                  temp_object=1,
                  resource_value=software_product,
                  quantity_unit=software_product.getQuantityUnit(),
                  software_type_value=software_type,
                  software_release_value=software_release,
                  start_date=start_date,
                  destination_project_value=project,
                  destination_value=destination,
                  price_currency="currency_module/EUR"
                )

                # Check Sale Supply Cell predicate configuration
                for sale_supply_line in sale_supply_line_list:
                  expected_test_result = (
                    (sale_supply_line.hasBasePrice()) and
                    (sale_supply_line.getPriceCurrency() == "currency_module/EUR") and
                    (software_product.getRelativeUrl() == sale_supply_line.getResource()) and
                    (project == sale_supply_line.getParentValue().getDestinationProjectValue()) and
                    ((sale_supply_line.getParentValue().getDestinationValue() is None) or
                     (destination == sale_supply_line.getParentValue().getDestinationValue())) and
                    (start_date == sale_supply_line.getParentValue().getStartDateRangeMin())
                  )
                  assert sale_supply_line.test(tmp_context) == expected_test_result, """Expected: %s %i %s
Product: %s %s
Project: %s %s
Destination: %s %s
Date: %s %s
""" % (
                    expected_test_result, i, sale_supply_line.getRelativeUrl(),
                    software_product.getRelativeUrl(), sale_supply_line.getResource(),
                    project.getRelativeUrl(), sale_supply_line.getParentValue().getDestinationProject(),
                    destination, sale_supply_line.getParentValue().getDestination(),
                    start_date, sale_supply_line.getParentValue().getStartDateRangeMin()
                  )
                  assert (sale_supply_line in domain_tool.searchPredicateList(
                          tmp_context, portal_type=['Sale Supply Line'])) == expected_test_result

                # Check Sale Supply Cell predicate configuration
                for sale_supply_cell in sale_supply_cell_list:
                  expected_test_result = (
                    (sale_supply_cell.hasBasePrice()) and
                    (sale_supply_cell.getPriceCurrency() == "currency_module/EUR") and
                    (software_product.getRelativeUrl() == sale_supply_cell.getResource()) and
                    (software_type.getRelativeUrl() == sale_supply_cell.getSoftwareType()) and
                    (software_release.getRelativeUrl() == sale_supply_cell.getSoftwareRelease()) and
                    (project == sale_supply_cell.getParentValue().getParentValue().getDestinationProjectValue()) and
                    ((sale_supply_cell.getParentValue().getParentValue().getDestinationValue() is None) or
                     (destination == sale_supply_cell.getParentValue().getParentValue().getDestinationValue())) and
                    (start_date == sale_supply_cell.getParentValue().getParentValue().getStartDateRangeMin())
                  )
                  assert sale_supply_cell.test(tmp_context) == expected_test_result, """Expected: %s %i %s
Product: %s %s
Type: %s %s
Release: %s %s
Project: %s %s
Destination: %s %s
Date: %s %s
""" % (
                    expected_test_result, i, sale_supply_cell.getRelativeUrl(),
                    software_product.getRelativeUrl(), sale_supply_cell.getResource(),
                    software_type.getRelativeUrl(), sale_supply_cell.getSoftwareType(),
                    software_release.getRelativeUrl(), sale_supply_cell.getSoftwareRelease(),
                    project.getRelativeUrl(), sale_supply_cell.getParentValue().getParentValue().getDestinationProject(),
                    destination, sale_supply_cell.getParentValue().getParentValue().getDestination(),
                    start_date, sale_supply_cell.getParentValue().getParentValue().getStartDateRangeMin()
                  )
                  assert (sale_supply_cell in domain_tool.searchPredicateList(
                          tmp_context, portal_type=['Sale Supply Cell'])) == expected_test_result

                  i += 1

    # New variation, to check the price when not Sale Supply Cell matching
    with_price_software_release = simple_product.contentValues(portal_type="Software Product Release Variation")[0]
    without_price_software_release = simple_product.newContent(
      portal_type="Software Product Release Variation",
      url_string="http://example.org/release_XX"
    )
    software_type = simple_product.contentValues(portal_type="Software Product Type Variation")[0]

    # Create movements
    # check getPrice
    for destination, project, software_release, date, expected_price in [
      (person_1, project_1, with_price_software_release, now, 24),
      (person_1, project_1, without_price_software_release, now, 22),
      (person_2, project_1, with_price_software_release, now, 14),
      (person_2, project_1, without_price_software_release, now, 12),
      (person_1, project_1, with_price_software_release, now - 1, None),
      (person_1, project_2, without_price_software_release, now, None),
    ]:
      resource_vcl = [
        'software_release/%s' % software_release.getRelativeUrl(),
        'software_type/%s' % software_type.getRelativeUrl()
      ]
      resource_vcl.sort()
      tmp_context = self.portal.portal_trash.newContent(
        portal_type='Sale Order Line',
        temp_object=1,
        resource_value=simple_product,
        variation_category_list=resource_vcl,
        start_date=date,
        destination_project_value=project,
        destination_value=destination,
        quantity_unit=software_product.getQuantityUnit(),
        price_currency="currency_module/EUR"
      )
      tmp_context = tmp_context.newContent(
        portal_type='Sale Order Cell',
        temp_object=1,
        software_type_value=software_type,
        software_release_value=software_release
      )#"""
      # Check that price is the predicate base price
      assert tmp_context.getPrice() == expected_price, """Expected:
Price: %s %s
Destination: %s
Project: %s
Software_release: %s
Date: %s
""" % (
      tmp_context.getPrice(), expected_price,
      destination, project, software_release, date
      )