portal = context.getPortalObject()
Base_translateString = portal.Base_translateString
instance_tree = context

software_product, _, software_type = instance_tree.InstanceTree_getSoftwareProduct()
expected_software_release = portal.portal_catalog.getResultValue(
    portal_type="Software Product Release Variation",
    url_string=target_software_release,
    parent_uid=software_product.getUid()
  )

upgrade_decision = context.InstanceTree_createUpgradeDecision(
  target_software_release=expected_software_release,
  target_software_type=software_type
)

if upgrade_decision is None:
  upgrade_decision = portal.portal_catalog.getResultValue(
    portal_type='Upgrade Decision',
    aggregate__uid=instance_tree.getUid(),
    simulation_state=['started', 'stopped', 'planned', 'confirmed']
  )
  if upgrade_decision is not None:
    # There is already a upgrade decision, do nothing
    return upgrade_decision.Base_redirect(
      dialog_id,
      keep_items={
        'portal_status_message': Base_translateString('There is already a pending Upgrade Decision'),
        'portal_status_level': 'error'
      }
    )

  upgrade_decision = portal.portal_catalog.getResultValue(
    portal_type='Upgrade Decision',
    aggregate__uid=instance_tree.getUid(),
    software_release__uid=expected_software_release.getUid(),
    simulation_state=['rejected']
  )
  if upgrade_decision is not None:
    # There is already a upgrade decision, do nothing
    return upgrade_decision.Base_redirect(
      dialog_id,
      keep_items={
        'portal_status_message': Base_translateString('There is already a rejected Upgrade Decision'),
        'portal_status_level': 'error'
      }
    )

  return context.Base_renderForm(
    dialog_id,
    Base_translateString('Can not propose an upgrade to this release'),
    level='error'
  )
else:
  return upgrade_decision.Base_redirect()
