assert context.getPortalType() == "Software Instance"
assert context.getValiationState() == "validated"
assert context.getSlapState() in ["start_requested", "stop_requested"]

context.renewCertificate()
