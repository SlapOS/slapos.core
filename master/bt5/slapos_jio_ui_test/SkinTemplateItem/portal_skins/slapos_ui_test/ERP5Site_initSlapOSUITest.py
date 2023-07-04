# PreferenceTool
from DateTime import DateTime

software_version = context.ERP5Site_getSoftwareReleaseTagVersion()

portal = context.getPortalObject()

preference = portal.portal_preferences.getActiveSystemPreference()
preference.edit(
  preferred_credential_alarm_automatic_call=1,
  preferred_credential_recovery_automatic_approval=1,
  preferred_credential_request_automatic_approval=1,
  preferred_authentication_policy_enabled=1
)

try:
  kvm_product = context.software_product_module["kvm"]
except KeyError:
  kvm_product = context.software_product_module.newContent(
    id="kvm",
    title="KVM",
    product_line ="software/application",
    reference="kvm",
    portal_type="Software Product"
  )

if kvm_product.getValidationState() == "draft":
  kvm_product.publish()

try:
  kvm_software_release = context.software_release_module["kvm"]
except KeyError:
  kvm_software_release = context.software_release_module.newContent(
    id="kvm",
    title="KVM",
    portal_type="Software Release",
    version="0.1",
    language="en",
    effective_date=DateTime('2018/03/14 00:00:00 UTC'),
    aggregate="software_product_module/kvm"
  )

kvm_software_release.edit(
  url_string="https://lab.nexedi.com/nexedi/slapos/raw/%s/software/kvm/software.cfg" % software_version,
)

if kvm_software_release.getValidationState() == "draft":
  kvm_software_release.publishAlive()

try:
  theia_product = context.software_product_module["theia"]
except KeyError:
  theia_product = context.software_product_module.newContent(
    id="theia",
    title="Theia",
    product_line ="software/application",
    reference="theia",
    portal_type="Software Product"
  )

if theia_product.getValidationState() == "draft":
  theia_product.publish()

try:
  theia_software_release = context.software_release_module["theia"]
except KeyError:
  theia_software_release = context.software_release_module.newContent(
    id="theia",
    title="Theia",
    portal_type="Software Release",
    version="0.1",
    language="en",
    effective_date=DateTime('2018/03/14 00:00:00 UTC'),
    aggregate="software_product_module/theia"

  )

theia_software_release.edit(
  url_string="https://lab.nexedi.com/nexedi/slapos/raw/%s/software/theia/software.cfg" % software_version
)

if theia_software_release.getValidationState() == "draft":
  theia_software_release.publishAlive()



try:
  erp5_product = context.software_product_module["erp5"]
except KeyError:
  erp5_product = context.software_product_module.newContent(
    id="erp5",
    title="ERP5",
    product_line ="software/application",
    reference="erp5",
    portal_type="Software Product"
  )

if erp5_product.getValidationState() == "draft":
  erp5_product.publish()

try:
  erp5_software_release = context.software_release_module["erp5"]
except KeyError:
  erp5_software_release = context.software_release_module.newContent(
    id="erp5",
    title="ERP5",
    portal_type="Software Release",
    version="0.1",
    language="en",
    effective_date=DateTime('2018/03/14 00:00:00 UTC'),
    aggregate="software_product_module/erp5"
  )

erp5_software_release.edit(
  url_string="https://lab.nexedi.com/nexedi/slapos/raw/%s/software/erp5/software.cfg" % software_version,
)

if erp5_software_release.getValidationState() == "draft":
  erp5_software_release.publishAlive()

# some are already indexed
kw = {'portal_type': ('Authentication Event', 'Passoword Event')}
for authentication_event in portal.portal_catalog(**kw):
  portal.system_event_module.manage_delObjects(ids=[authentication_event.getId()])

notification_message_to_enable = [
  'slapos-upgrade-instance-tree.notification',
  'slapos-upgrade-delivered-instance-tree.notification',
  'slapos-upgrade-compute-node.notification',
  'slapos-upgrade-delivered-compute-node.notification',
]

for reference in notification_message_to_enable:
  search_kw = dict(portal_type='Notification Message',
    reference=reference)
  if not len(portal.portal_catalog(validation_state='validated', **search_kw)):
    portal.portal_catalog.getResultValue(validation_state='draft',
      **search_kw).validate()

# Create an manager user
try:
  demo_manager_user = context.person_module["demo_manager_user"]
except KeyError:
  demo_manager_user = context.person_module.newContent(
    id="demo_manager_user",
    title="Demo Manager Functional User",
    portal_type="Person",
    email="x@example.com"
  )

try:
  demo_manager_assignment = demo_manager_user["manager_assignment"]
except KeyError:
  demo_manager_assignment = demo_manager_user.newContent(
    id="manager_assignment",
    title="Demo Manager Functional User Assignment",
    portal_type="Assignment",
  )

demo_manager_assignment.setGroup('company')

if demo_manager_assignment.getValidationState() != "open":
  demo_manager_assignment.open()

try:
  demo_manager_login = demo_manager_user["demo_manager_login"]
except KeyError:
  demo_manager_login = demo_manager_user.newContent(
    id="demo_manager_login",
    portal_type="ERP5 Login",
    reference="demo_manager_functional_user"
  )
  demo_manager_login.setPassword("czz4yt36mshT*")

if demo_manager_login.getValidationState() != "validated":
  demo_manager_login.validate()

return "Done."
