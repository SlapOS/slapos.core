# PreferenceTool
from DateTime import DateTime

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
  url_string="https://lab.nexedi.com/nexedi/slapos/raw/1.0.164/software/kvm/software.cfg",
)

if kvm_software_release.getValidationState() == "draft":
  kvm_software_release.publishAlive()

try:
  slaprunner_product = context.software_product_module["slaprunner"]
except KeyError:
  slaprunner_product = context.software_product_module.newContent(
    id="slaprunner",
    title="Webrunner",
    product_line ="software/application",
    reference="slaprunner",
    portal_type="Software Product"
  )

if slaprunner_product.getValidationState() == "draft":
  slaprunner_product.publish()

try:
  slaprunner_software_release = context.software_release_module["slaprunner"]
except KeyError:
  slaprunner_software_release = context.software_release_module.newContent(
    id="slaprunner",
    title="Webrunner",
    portal_type="Software Release",
    version="0.1",
    language="en",
    effective_date=DateTime('2018/03/14 00:00:00 UTC'),
    aggregate="software_product_module/slaprunner"

  )

slaprunner_software_release.edit(
  url_string="https://lab.nexedi.com/nexedi/slapos/raw/1.0.164/software/slaprunner/software.cfg"
)

if slaprunner_software_release.getValidationState() == "draft":
  slaprunner_software_release.publishAlive()

portal = context.getPortalObject()

# some are already indexed
kw = {'portal_type': ('Authentication Event', 'Passoword Event')}
for authentication_event in portal.portal_catalog(**kw):
  portal.system_event_module.manage_delObjects(ids=[authentication_event.getId()])

return "Done."
