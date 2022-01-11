# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName


class TestSlapOSAllocationSupply(SlapOSTestCaseMixin):

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
      title="Simple Product"
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

    # create 1 compute node
    compute_node_1 = self.portal.compute_node_module.newContent(
      portal_type="Compute Node"
    )

    # Create 2 allocation supplies
    # - one for everybody (no destination)
    # - one for one specific user
    now = DateTime()
    everybody_supply = self.portal.allocation_supply_module.newContent(
      title="Everybody Supply",
      start_date_range_min=now,
      destination_project_value=project_1,
      aggregate_value=compute_node_1
    )
    person_1_supply = self.portal.allocation_supply_module.newContent(
      title="Person 1 Supply",
      start_date_range_min=now,
      destination_project_value=project_1,
      aggregate_value=compute_node_1,
      destination_value=person_1
    )

    # Create Allocation Line/Cell for all product combination
    allocation_supply_cell_list = []
    base_id = 'path'
    for allocation_supply in [everybody_supply, person_1_supply]:
      for software_product in [simple_product, complex_product]:
        allocation_supply_line = allocation_supply.newContent(
          portal_type="Allocation Supply Line",
          resource_value=software_product
        )
        allocation_supply_line.edit(
          p_variation_base_category_list=allocation_supply_line.getVariationRangeBaseCategoryList()
        )
        allocation_supply_line.setCellRange(
          base_id=base_id,
          *allocation_supply_line.SupplyLine_asCellRange(base_id=base_id)
        )
        for cell_key in list(allocation_supply_line.getCellKeyList(base_id=base_id)):
          allocation_supply_cell = allocation_supply_line.newCell(
            base_id=base_id,
            portal_type='Allocation Supply Cell',
            *cell_key
          )
          allocation_supply_cell.edit(
            mapped_value_property_list=['allocable'],
            allocable=True,
            predicate_category_list=cell_key,
            variation_category_list=cell_key
          )
          allocation_supply_cell_list.append(allocation_supply_cell)
      allocation_supply.validate()

    self.tic()
    # Create 2 movements
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
                  software_type_value=software_type,
                  software_release_value=software_release,
                  start_date=start_date,
                  destination_project_value=project,
                  destination_value=destination
                )
                for allocation_supply_cell in allocation_supply_cell_list:
                  expected_test_result = (
                    (software_product.getRelativeUrl() == allocation_supply_cell.getResource()) and
                    (software_type.getRelativeUrl() == allocation_supply_cell.getSoftwareType()) and
                    (software_release.getRelativeUrl() == allocation_supply_cell.getSoftwareRelease()) and
                    (project == allocation_supply_cell.getParentValue().getParentValue().getDestinationProjectValue()) and
                    ((allocation_supply_cell.getParentValue().getParentValue().getDestinationValue() is None) or
                     (destination == allocation_supply_cell.getParentValue().getParentValue().getDestinationValue())) and
                    (start_date == allocation_supply_cell.getParentValue().getParentValue().getStartDateRangeMin())
                  )
                  assert allocation_supply_cell.test(tmp_context) == expected_test_result, """Expected: %s %i
Product: %s %s
Type: %s %s
Release: %s %s
Project: %s %s
Destination: %s %s
Date: %s %s
""" % (
                    expected_test_result, i,
                    software_product.getRelativeUrl(), allocation_supply_cell.getResource(),
                    software_type.getRelativeUrl(), allocation_supply_cell.getSoftwareType(),
                    software_release.getRelativeUrl(), allocation_supply_cell.getSoftwareRelease(),
                    project.getRelativeUrl(),allocation_supply_cell.getParentValue().getParentValue().getDestinationProject(),
                    destination, allocation_supply_cell.getParentValue().getParentValue().getDestination(),
                    start_date, allocation_supply_cell.getParentValue().getParentValue().getStartDateRangeMin()
                  )
                  assert (allocation_supply_cell in domain_tool.searchPredicateList(
                          tmp_context, portal_type=['Allocation Supply Cell'])) == expected_test_result
                  i += 1
