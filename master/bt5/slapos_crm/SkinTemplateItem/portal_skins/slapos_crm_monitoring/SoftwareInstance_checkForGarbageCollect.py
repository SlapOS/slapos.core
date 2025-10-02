instance = context
portal = context.getPortalObject()
project= instance.getFollowUpValue()
instance_tree = instance.getSpecialiseValue(portal_type='Instance Tree')

if (instance.getPortalType() != "Software Instance"):
  return
if instance.getValidationState() != 'invalidated':
  raise NotImplementedError('Instance %s is not supposed to be validated again' % instance.getRelativeUrl())
if instance_tree.getValidationState() != 'validated':
  # Instance tree was invalidated, nothing to do
  return

# Search destroyed instances with non destroyed sub instance
garbage_collect_list = []

instance_tree_relative_url = instance_tree.getRelativeUrl()
for sub_instance in instance.getSuccessorValueList():
  if sub_instance.getSlapState() != 'destroy_requested':
    garbage_collect_list.append(sub_instance)

# Create tickets
if garbage_collect_list:
  ticket_title = 'Instance tree %s contains instances to garbage collect' % instance_tree.getReference()
  ticket_description = """This instance tree contains instances which seem not used anymore.

Here is the list:
%s

Please destroyed them, or request them from another parent instance.
""" % '\n'.join(['- %s %s' % (x.getReference(), x.getTitle()) for x in garbage_collect_list])

  support_request = project.Project_createTicketWithCausality(
    'Support Request',
    ticket_title,
    ticket_description,
    causality=instance_tree_relative_url,
    destination_decision=instance_tree.getDestinationSection()
  )

  if support_request is not None:
    event = support_request.Ticket_createProjectEvent(
      ticket_title, 'outgoing', 'Web Message',
      portal.service_module.slapos_crm_information.getRelativeUrl(),
      ticket_description,
      content_type='text/plain',
      #notification_message=error_dict['notification_message_reference'],
      #language=XXX,
      #substitution_method_parameter_dict=error_dict
    )
    support_request.reindexObject(activate_kw=activate_kw)
    event.reindexObject(activate_kw=activate_kw)
    return support_request
