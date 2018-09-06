from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

subscription_condition = context.portal_catalog(
  portal_type="Subscription Condition",
  reference=subscription_reference,
  validation_state="validated")

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
)
