computer = state_change['object']
context.REQUEST.set('computer_certificate', None)
context.REQUEST.set('computer_certificate_url', None)
destination_reference = computer.getDestinationReference()
if destination_reference is None:
  raise ValueError('No certificate')
context.getPortalObject().portal_web_services.caucase_adapter\
  .revokeCertificate(destination_reference)
computer.setDestinationReference(None)
