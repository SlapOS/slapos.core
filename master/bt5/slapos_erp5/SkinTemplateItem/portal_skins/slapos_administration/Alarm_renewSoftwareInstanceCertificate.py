context.getPortalObject().portal_catalog.searchAndActivate(
      method_id='SoftwareInstance_renewCertificate',
      activate_kw=dict(tag=tag, priority=5),
      portal_type="Software Instance",
      validation_state="validated",
      **{"slap_item.slap_state": ["start_requested", "stop_requested"]})
