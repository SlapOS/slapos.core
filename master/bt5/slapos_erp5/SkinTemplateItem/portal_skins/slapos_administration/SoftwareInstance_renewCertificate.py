if (context.getPortalType() == "Software Instance" and \
    context.getValiationState() == "validated" and \
    context.getSlapState() in ["start_requested", "stop_requested"]):
  context.revokeCertificate()
  context.generateCertificate()
