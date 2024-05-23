fixit = True if fixit else False
error_list = []
portal = context.getPortalObject()
portal_categories = portal.portal_categories

configured_module_name_list = []

# XXX Find a nice way to store the "json", and then create make a generic erp5_upgrader constraint
#     Or may be let the configurator set these values, and change this script to check BA against the configurator
for business_application_id, module_name_list in [
      ["base", [  # Base Data
          "organisation_module",
          "person_module",
        ]],
      ["accounting", [  # Accounting
          "accounting_module",
          "account_module",
          "currency_module",
      ]],
      ["login", [  # Login
          "access_token_module",
          "credential_request_module",
          "credential_recovery_module",
          "credential_update_module",
          "system_event_module",
      ]],
      ["slapos", [  # SlapOS
          "allocation_supply_module",
          "cloud_contract_module",
          "compute_node_module",
          "computer_module",
          "computer_model_module",
          "computer_network_module",
          "consumption_document_module",
          "data_set_module",
          "hosting_subscription_module",
          "instance_tree_module",
          "invitation_token_module",
          "project_module",
          "software_installation_module",
          "software_instance_module",
          "subscription_request_module",
          "subscription_change_request_module",
      ]],
      ["crm", [  # Customer Relation Management
          "campaign_module",
          "event_module",
          "incident_response_module",
          "notification_message_module",
          "meeting_module",
          "sale_opportunity_module",
          "support_request_module",
          "regularisation_request_module",
          "upgrade_decision_module"
      ]],
      ["dms", [  # Knowledge management
          "document_module",
          "document_ingestion_module",
          "image_module",
          "web_page_module",
          "web_site_module"
        ]],
      ["pdm", [  # PDM
          "component_module",
          "software_release_module",
          "software_product_module",
          "software_publication_module",
          "software_licence_module",
          "product_module",
          "service_module",
          "transformation_module",
        ]],
      ["trade", [  # Trade
          "business_process_module",
          "business_configuration_module",
          "inventory_module",
          "purchase_order_module",
          "purchase_packing_list_module",
          "purchase_supply_module",
          "purchase_trade_condition_module",
          "open_sale_order_module",
          "sale_order_module",
          "sale_packing_list_module",
          "sale_supply_module",
          "sale_trade_condition_module",
        ]],
    ]:
  for module_name in module_name_list:
    configured_module_name_list.append(module_name)
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
      current_business_application_id = module.getBusinessApplication(None)
    except AttributeError:
      current_business_application_id = None
      raise AttributeError("%s has no business_application category" % (module_name))
    if current_business_application_id != business_application_id:
      if fixit:
        module.setBusinessApplicationValue(business_application_value)
      else:
        error_list.append("no business application assigned to module %s (Expected: %s | Found: %s)" % (module_name, business_application_id, current_business_application_id))

# Remove business application from unused module
for module_name in portal.contentIds():
  if module_name.endswith("_module") and (module_name not in configured_module_name_list):
    module = getattr(portal, module_name, None)
    if module is None:
      if not fixit:
        error_list.append("module %s not found, please update this constraint! (ignored when solving)" % module_name)
      continue
    try:
      current_business_application_id = module.getBusinessApplication(None)
    except AttributeError:
      current_business_application_id = None
    if current_business_application_id != None:
      if fixit:
        module.setBusinessApplicationValue(None)
      else:
        error_list.append("no business application assigned to module %s (Expected: None | Found: %s)" % (module_name, current_business_application_id))

#return "\n".join(error_list) or "OK"
return error_list
