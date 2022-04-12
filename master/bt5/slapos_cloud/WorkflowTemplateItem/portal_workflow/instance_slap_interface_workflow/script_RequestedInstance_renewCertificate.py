instance = state_change['object']
portal = instance.getPortalObject()

assert instance.getPortalType() == 'Software Instance'
assert instance.getValidationState() == 'validated'

# Only instances with workflow can renew it.
if (instance.getSslKey() is None) and (instance.getSslCertificate() is None):
  raise NotImplementedError('No certificates on the instance')

if not instance.getDestinationReference():
  raise NotImplementedError('No certificiate reference')

instance.revokeCertificate()
instance.generateCertificate()
