from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

# Set AcceptLanguage in the REQUEST so that getDefaultLanguage() can work
if target_language and context.REQUEST.get('AcceptLanguage'):
  context.REQUEST['AcceptLanguage'].set(target_language, 10)

if context.getSimulationState() not in ["draft", "planned"]:
  # Don't modify it anymore
  return

if subscription_condition_reference is not None:
  raise NotImplementedError(subscription_condition_reference)
  # It would be better use some clever API here.
  if target_language == "zh":
    subscription_condition_reference += "_zh"
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

email = context.getDestinationSectionValue().getDefaultEmailText()
now = DateTime()

context.edit(
  title="Subscription %s for %s" % (subscription_condition.getTitle(), email),
  #url_string=subscription_condition.getUrlString(),
  #text_content=instance_xml,
  #sla_xml=subscription_condition.getSlaXml(),
  start_date=now,
  #root_slave=subscription_condition.getRootSlave(),
  specialise_value=subscription_condition,
  #price=subscription_condition.getPrice(),
  #price_currency=subscription_condition.getPriceCurrency(),

  # Set Provider from Subscription Condition
  #source=subscription_condition.getSource(),
  #source_section=subscription_condition.getSourceSection()
)

context.setSourceReference(subscription_condition.getSourceReference())
