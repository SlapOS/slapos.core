portal = context.getPortalObject()
erp5_login = portal.portal_catalog.getResultValue(
  portal_type="ERP5 Login",
  reference="free_trial_user",
  validation_state="validated")

if erp5_login is None:
  return

person = erp5_login.getParentValue()

if context.getSpecialise() is not None:
  return

if context.getValidationState() == "validated":
  return

if context.getUrlString() is None:
  # Nothing to request here
  return

state = "started"

request_kw = {}
request_kw.update(
    software_release=context.getUrlString(),
    software_title=context.getTitle() + " %s" % str(context.getUid()),
    software_type=context.getSourceReference(),
    instance_xml=context.getTextContent(),
    sla_xml=context.getSlaXml(""),
    shared=context.getRootSlave(False),
    state=state,
  )

person.requestSoftwareInstance(**request_kw)

requested_software_instance = context.REQUEST.get('request_instance')

if requested_software_instance is None:
  return

context.setAggregateValue(requested_software_instance)

context.setSpecialise(
  requested_software_instance.getSpecialise())

if context.getValidationState() == "draft":
  context.submit()

return
