from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

if context.getSimulationState() not in ["draft", "planned"]:
  # Don't modify it anymore
  return

subscription_condition = context.getSpecialiseValue()

if subscription_condition is None:
  raise ValueError(
    "It was not possible to find the appropriate Condition for this Subscription")

# Get Subscription condition for this Subscription Request

context.edit(
  title="Subscription %s for %s" % (subscription_condition.getTitle(), context.getDestinationSectionValue().getDefaultEmailText()),
  #url_string=subscription_condition.getUrlString(),
  #text_content=instance_xml,
  #sla_xml=subscription_condition.getSlaXml(),
  start_date=DateTime(),
  #root_slave=subscription_condition.getRootSlave(),
  specialise_value=subscription_condition,
  #price=subscription_condition.getPrice(),
  #price_currency=subscription_condition.getPriceCurrency(),

  # Set Provider from Subscription Condition
  #source=subscription_condition.getSource(),
  #source_section=subscription_condition.getSourceSection()
  source_reference=subscription_condition.getSourceReference()
)
