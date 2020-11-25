fixit = True if fixit else False
error_list = []
portal = context.getPortalObject()
portal_categories = portal.portal_categories

# XXX Find a nice way to store the "json", and then create make a generic erp5_upgrader constraint
#     Or may be let the configurator set these values, and change this script to check BA against the configurator
for business_application_id, module_name_list in [
      ["base", [  # Base Data
          "currency_module",
          "organisation_module",
          "person_module",
          "access_token_module",
          "invitation_token_module",
          "credential_request_module"
        ]],
      ["accounting", [  # Accounting
        "accounting_module",
        "account_module"
        ]],
      ["crm", [  # Customer Relation Management
          "campaign_module",
          "event_module",
          "system_event_module",
          "meeting_module",
          "sale_opportunity_module",
          "support_request_module",
          "regularisation_request_module",
          "upgrade_decision_module"
      ]],
      ["dms", [  # Knowledge management
          "document_ingestion_module",
          "test_page_module",
          "web_page_module",
          "web_site_module"
        ]],
      ["pdm", [  # PDM
          "software_release_module",
          "software_product_module",
          "software_publication_module",
          "software_licence_module",
          "product_module",
          "service_module"
        ]],
      ["trade", [  # Trade
          "internal_order_module",
          "internal_packing_list_module",
          "internal_supply_module",
          "inventory_module",
          "purchase_order_module",
          "purchase_packing_list_module",
          "purchase_supply_module",
          "purchase_trade_condition_module",
          "open_purchase_order_module",
          "open_sale_order_module",
          "open_internal_order_module",
          "returned_sale_packing_list_module",
          "returned_sale_order_module",
          "returned_purchase_packing_list_module",
          "returned_purchase_order_module",
          "sale_order_module",
          "sale_packing_list_module",
          "sale_supply_module",
          "sale_trade_condition_module",
        ]],
    ]:
  for module_name in module_name_list:
    module = getattr(portal, module_name, None)
    if module is None:
      if not fixit:
        error_list.append("module %s not found, please update this constraint! (ignored when solving)" % module_name)
      continue
    try:
      business_application_value = portal_categories.restrictedTraverse("business_application/" + business_application_id)
    except KeyError:
      if not fixit:
        error_list.append("business application %s not found, please update this constraint! (ignored when solving)" % business_application_id)
      continue
    try:
      module.getBusinessApplication(None)
    except AttributeError:
      raise AttributeError("%s has no business_application category" % (module_name))
    if module.getBusinessApplication(None) != business_application_id:
      if fixit:
        module.setBusinessApplicationValue(business_application_value)
      else:
        error_list.append("no business application assigned to module %s (Expected: %s | Found: %s)" % (module_name, business_application_id, module.getBusinessApplication(None)))

#return "\n".join(error_list) or "OK"
return error_list
