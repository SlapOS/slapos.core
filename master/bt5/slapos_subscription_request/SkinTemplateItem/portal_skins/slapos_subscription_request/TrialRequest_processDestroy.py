portal = context.getPortalObject()
erp5_login = portal.portal_catalog.getResultValue(
  portal_type="ERP5 Login",
  reference="free_trial_user",
  validation_state="validated")

if erp5_login is None:
  return

person = erp5_login.getParentValue()

if context.getStopDate() >= DateTime():
  return

if person is None:
  return

if context.getSpecialise() is None:
  return

if context.getValidationState() != "validated":
  return

state = 'destroyed'

instance_tree = context.getSpecialiseValue()

request_kw = {}
request_kw.update(
    software_release=instance_tree.getUrlString(),
    software_title=instance_tree.getTitle(),
    software_type=instance_tree.getSourceReference(),
    instance_xml=instance_tree.getTextContent(),
    sla_xml="",
    shared=instance_tree.getRootSlave(),
    state=state,
  )

person.requestSoftwareInstance(**request_kw)

assert instance_tree.getSlapState() == "destroy_requested",\
  "Instance Tree not destroyed!!"

connection_dict = instance_tree.getSuccessorValue().getConnectionXmlAsDict()

connection_key_list = context.getSubjectList()
connection_string = '\n'.join(['%s: %s' % (x,y) for x,y in connection_dict.items() if x in connection_key_list])

mapping_dict = {"token": connection_string }


context.TrialRequest_sendMailMessage(person,
    context.getDefaultEmailText(),
   'slapos-free.trial.destroy',
   mapping_dict)

context.invalidate()
