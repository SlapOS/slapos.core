from AccessControl import ClassSecurityInfo, Unauthorized, getSecurityManager
from Products.ERP5.Document.Person import Person as ERP5Person
from Products.ERP5Type import Permissions

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

  def getPersonCertificateList(self):
    return [x for x in
      self.contentValues(portal_type="Certificate Access ID")
      if x.getValidationState() == 'validated']

  security.declarePublic('signCertificate')
  def signCertificate(self, csr):
    """Send csr for certificate signature"""
    self._checkCertificateRequest()
    if len(self.getPersonCertificateList()):
      raise ValueError("A Certificate already exists, please revoke it first!")
    ca_service = self.getPortalObject().portal_web_services.caucase_adapter
    csr_id = ca_service.putCertificateSigningRequest(csr)

    # Sign the csr immediately
    crt_id, url = ca_service.signCertificate(csr_id)

    # link to the user
    certificate_id = self.newContent(
      portal_type="Certificate Access ID",
      reference=crt_id,
      url_string=url)

    certificate_id.validate()
    return crt_id, url

  security.declarePublic('getCertificate')
  def getCertificate(self):
    """Returns existing SSL certificate"""
    self._checkCertificateRequest()
    crt_id_list = self.getPersonCertificateList()
    if crt_id_list:
      # XXX - considering there is only one certificate per user
      return self.getPortalObject().portal_web_services.caucase_adapter\
        .getCertificate(crt_id_list[0].getReference())
    raise ValueError(
      "No certificate set for the user %s" % self.getReference()
    )

  security.declarePublic('revokeCertificate')
  def revokeCertificate(self):
    """Revokes existing certificate"""
    self._checkCertificateRequest()
    crt_id_list = self.getPersonCertificateList()
    if crt_id_list:
      # XXX - considering there is only one certificate per user
      certificate_id = crt_id_list[0]
      response = self.getPortalObject().portal_web_services.caucase_adapter\
        .revokeCertificate(certificate_id.getReference())
      # Invalidate certificate id of the user
      certificate_id.invalidate()
      return response
    raise ValueError(
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
