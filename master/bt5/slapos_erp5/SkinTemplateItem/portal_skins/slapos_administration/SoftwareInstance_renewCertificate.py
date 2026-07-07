if (context.getPortalType() == "Software Instance" and \
    context.getValidationState() == "validated" and \
    context.getSlapState() in ["start_requested", "stop_requested"]):
  context.revokeCertificate()
  context.generateCertificate()
  context.reindexObject(activate_kw=activate_kw)
