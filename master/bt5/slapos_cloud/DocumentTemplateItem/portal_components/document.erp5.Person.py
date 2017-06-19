from AccessControl import ClassSecurityInfo, Unauthorized, getSecurityManager
from Products.ERP5.Document.Person import Person as ERP5Person
from Products.ERP5Type import Permissions

class UserCertificateNotFound(Exception):
  """Exception raised when certificate is not found"""
  pass

class UserCertificateFound(Exception):
  """Exception raised when certificate is found"""
  pass

class Person(ERP5Person):
  security = ClassSecurityInfo()

  def _checkCertificateRequest(self):
    try:
      self.checkUserCanChangePassword()
    except Unauthorized:
      # in ERP5 user has no SetOwnPassword permission on Person document
      # referring himself, so implement "security" by checking that currently
      # logged in user is trying to get/revoke his own certificate
      reference = self.getReference()
      if not reference:
        raise
      if getSecurityManager().getUser().getId() != reference:
        raise

  security.declarePublic('signCertificate')
  def signCertificate(self, csr):
    """Send csr for certificate signature"""
    self._checkCertificateRequest()
    if self.getDestinationReference():
      raise UserCertificateFound("A Certificate already exists, please revoke it first!")
    ca_service = self.getPortalObject().portal_web_services.caucase_adapter
    csr_id = ca_service.putCertificateSigningRequest(csr)

    # Sign the csr immediately
    crt_id, url = ca_service.signCertificate(csr_id)
    self.setDestinationReference(crt_id)
    return crt_id, url

  security.declarePublic('getCertificate')
  def getCertificate(self):
    """Returns existing SSL certificate"""
    self._checkCertificateRequest()
    crt_id = self.getDestinationReference()
    if crt_id:
      return self.getPortalObject().portal_web_services.caucase_adapter\
        .getCertificate(crt_id)
    raise UserCertificateNotFound(
      "No certificate set for the user %s" % self.getReference()
    )

  security.declarePublic('revokeCertificate')
  def revokeCertificate(self):
    """Revokes existing certificate"""
    self._checkCertificateRequest()
    crt_id = self.getDestinationReference()
    if crt_id:
      response = self.getPortalObject().portal_web_services.caucase_adapter\
        .revokeCertificate(crt_id)
      # Remove Destination Reference
      self.setDestinationReference("")
      return response.read()
    raise UserCertificateNotFound(
      "No certificate set for the user %s" % self.getReference()
    )

  security.declareProtected(Permissions.AccessContentsInformation,
                            'getTitle')
  def getTitle(self, **kw):
    """
      Returns the title if it exists or a combination of
      first name and last name
    """
    title = ERP5Person.getTitle(self, **kw)
    test_title = title.replace(' ', '')
    if test_title == '':
      return self.getDefaultEmailCoordinateText(test_title)
    else:
      return title
