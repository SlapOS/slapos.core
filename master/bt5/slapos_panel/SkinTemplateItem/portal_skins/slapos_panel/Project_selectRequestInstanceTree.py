from zExceptions import Unauthorized

portal = context.getPortalObject()

if shared in ["true", "1", 1]:
  shared = True

if shared in ["false", "", 0, "0", None]:
  shared = False

if "{uid}" in title:
  uid_ = portal.portal_ids.generateNewId(id_group=("vifib", "kvm"), default=1)
  title = title.replace("{uid}", str(uid_))
"""
instance_tree = portal.portal_catalog.getResultValue(
  portal_type='Instance Tree',
  validation_state="validated",

  title={'query': title, 'key': 'ExactMatch'}
  )

if instance_tree is not None:
  response.setStatus(409)
  return "Instance with this name already exists"
"""

person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person is None:
  raise Unauthorized("You cannot request without been logged in as a user.")

if software_type in [None, ""]:
  raise ValueError("Software Type value was not propagated")

if text_content in ["", None]:
  text_content = """<?xml version='1.0' encoding='utf-8' ?>
<instance>
</instance>"""

request_kw = {}
request_kw.update(
  software_release=url_string,
  software_title=title,
  software_type=software_type,
  instance_xml=text_content,
  sla_xml="",
  shared=shared,
  state="started",
  project_reference=context.getReference()
)

for sla_category_id, sla_category in [
  ('computer_guid', computer_guid),
]:
  if sla_category:
    sla_xml += '<parameter id="%s">%s</parameter>' % (sla_category_id, sla_category)

if sla_xml:
  request_kw['sla_xml'] = """<?xml version='1.0' encoding='utf-8'?>
<instance>
%s
</instance>""" % sla_xml

person.requestSoftwareInstance(**request_kw)
request_instance_tree = context.REQUEST.get('request_instance_tree')

web_site = context.getWebSectionValue()
assert web_site is not None

# Evaluate if the user has to pay something,
# Since we need access to organisation_module on Entity_getDepositBalanceAmount
# evaluate as Shadow User.
subscription_request = request_instance_tree.Item_createSubscriptionRequest(temp_object=True)

# Check if we could create the Subscription Request
if subscription_request is not None:
  price = subscription_request.getPrice(None)
  # If the payment is done by an Organisation, skip user payment process
  if (price is not None) and (price != 0) and (subscription_request.getDestinationSection() == person.getRelativeUrl()):
    balance = person.Entity_getDepositBalanceAmount([subscription_request])
    if balance < price:
      instance = web_site.restrictedTraverse(request_instance_tree.getRelativeUrl())
      return instance.Base_renderForm(
        "InstanceTree_viewCreateDirectDepositPaymentTransactionOnSlaposPanelDialog",
	      message=context.Base_translateString("Your instance is created, please proceed to payment.")
      )

return request_instance_tree.Base_redirect()
