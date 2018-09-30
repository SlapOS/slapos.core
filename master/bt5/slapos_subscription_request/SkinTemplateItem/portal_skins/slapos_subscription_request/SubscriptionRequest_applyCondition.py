from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

if context.getSimulationState() not in ["draft", "planned"]:
  # Don't modify it anymore
  return

if subscription_condition_reference is not None:
  # It would be better use some clever API here.
  subscription_condition = context.portal_catalog.getResultValue(
    portal_type="Subscription Condition",
    reference=subscription_condition_reference,
    validation_state="validated")
else:
  subscription_condition = context.getSpecialiseValue()

if subscription_condition is None:
  raise ValueError(
    "It was not possible to find the appropriate Condition %s for this Subscription" \
      % subscription_condition_reference)

# Get Subscription condition for this Subscription Request
subscription_configuration = {
    "instance_xml": subscription_condition.getTextContent(),
    "software_type": subscription_condition.getSourceReference(),
    "url": subscription_condition.getUrlString(),
    "shared": subscription_condition.getRootSlave(),
    "subject_list": subscription_condition.getSubjectList(),
    "sla_xml": subscription_condition.getSlaXml(),
    "specialise": subscription_condition.getRelativeUrl()
}

email = context.getDestinationSectionValue().getDefaultEmailText()
now = DateTime()

context.edit(
  source_reference=subscription_configuration["software_type"],
  title="Subscription %s for %s" % (subscription_condition.getTitle(), email),
  url_string=subscription_configuration["url"],
  text_content=subscription_configuration["instance_xml"],
  start_date=now,
  root_slave=subscription_configuration["shared"],
  subject_list=subscription_configuration["subject_list"],
  specialise_value=subscription_condition
)
