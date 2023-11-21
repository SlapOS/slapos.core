from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

support_request = context
portal = context.getPortalObject()
portal_categories = portal.portal_categories

category_list = support_request.getCategoryList()

is_migration_needed = False
causality_relative_url = None
causality_value = None
for category in category_list:
  base_category, category_relative_url = category.split('/', 1)
  if ('module' in category_relative_url) and \
     (category_relative_url.split('/', 1)[0] not in ['currency_module', 'event_module', 'person_module', 'organisation_module', 'service_module', 'project_module', 'sale_trade_condition_module', 'incident_response_module']):
    category_value = portal_categories.getCategoryValue(category_relative_url, base_category=base_category)
    # Normally, the causality is spotted
    if (base_category != 'causality') and (category_value.getPortalType() != 'Category'):
      is_migration_needed = True
      causality_relative_url = category_relative_url

if not is_migration_needed:
  causality_value = support_request.getCausalityValue()
  if (causality_value is None) or (causality_value.getPortalType() in portal.getPortalEventTypeList()):
    causality_relative_url = support_request.getDestinationDecision(portal_type='Person', default=None)
    if causality_relative_url is None:
      causality_relative_url = support_request.getSource(portal_type='Person', default=None)
    if causality_relative_url is None:
      causality_relative_url = support_request.getAggregate(portal_type='Person', default=None)

    if causality_relative_url is not None:
      is_migration_needed = True

if is_migration_needed:
  support_request.activate(activate_kw=activate_kw).Base_activateObjectMigrationToVirtualMaster(causality_relative_url)
else:
  if not ((len(category_list) == 0) or (support_request.getSimulationState() in ['draft', 'deleted']) or (causality_value is not None)):
    # debug
    context.log('COULD NOT MIGRATE %s' % support_request.getRelativeUrl())
