portal = context.getPortalObject()
Base_translateString = portal.Base_translateString
instance_tree = context

software_product, _, software_type = instance_tree.InstanceTree_getSoftwareProduct()

upgrade_decision = context.InstanceTree_createUpgradeDecision(
  target_software_release=portal.portal_catalog.getResultValue(
      portal_type="Software Product Release Variation",
      url_string=target_software_release,
      parent_uid=software_product.getUid()
    ),
  target_software_type=software_type
)

if upgrade_decision is None:
  return context.Base_renderForm(dialog_id, Base_translateString('Can not propose an upgrade to this release'), level='error')
else:
  return upgrade_decision.Base_redirect()
