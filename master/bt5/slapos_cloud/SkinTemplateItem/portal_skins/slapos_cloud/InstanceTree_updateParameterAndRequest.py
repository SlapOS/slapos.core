from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

request_instance_tree = context
software_release_url_string = software_release
root_state = state
is_slave = shared
if is_slave not in [True, False]:
  raise ValueError("shared should be a boolean")

promise_kw = {
  'instance_xml': instance_xml,
  'software_type': software_type,
  'sla_xml': sla_xml,
  'software_release': software_release_url_string,
  'shared': is_slave,
}

# Change desired state
if (root_state == "started"):
  request_instance_tree.requestStart(**promise_kw)
elif (root_state == "stopped"):
  request_instance_tree.requestStop(**promise_kw)
elif (root_state == "destroyed"):
  request_instance_tree.requestDestroy(**promise_kw)
  context.REQUEST.set('request_instance_tree', None)
else:
  raise ValueError("state should be started, stopped or destroyed")

request_instance_tree.requestInstance(
  software_release=software_release_url_string,
  software_title=software_title,
  software_type=software_type,
  instance_xml=instance_xml,
  sla_xml=sla_xml,
  shared=is_slave,
  state=root_state,
)

# Change the state at the end to allow to execute updateLocalRoles only once in the transaction
validation_state = request_instance_tree.getValidationState()
slap_state = request_instance_tree.getSlapState()
if validation_state == 'draft':
  request_instance_tree.portal_workflow.doActionFor(request_instance_tree,
                                           'validate_action')
if (validation_state != 'archived') and \
   (slap_state == 'destroy_requested'):
  # XXX TODO do not use validation workflow to filter destroyed subscription
  request_instance_tree.archive()
