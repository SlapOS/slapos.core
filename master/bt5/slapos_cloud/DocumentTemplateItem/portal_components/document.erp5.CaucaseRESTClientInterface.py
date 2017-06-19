##############################################################################
#
# Copyright (c) 2002-2010 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.
#
##############################################################################

from AccessControl import ClassSecurityInfo
from Products.ERP5Type.Globals import InitializeClass
from Products.ERP5Type import Permissions
from Products.ERP5Type.XMLObject import XMLObject
from DateTime import DateTime
import functools
from json import loads, dumps
import urllib2, urllib
from httplib import HTTPSConnection
import urlparse
from zLOG import LOG, INFO

class TolerateErrorHandler(urllib2.BaseHandler):
  handler_order = 100 # Get registered before default error hander (at 500)
  def http_error_default(self, req, fp, code, msg, hdrs):
    return fp

class BoundHTTPSHandler(urllib2.HTTPSHandler):
  def __init__(self, source_address=None, **kw):
    urllib2.HTTPSHandler.__init__(self, **kw)
    connection_kw = {}
    if source_address is not None:
      connection_kw['source_address'] = (source_address, 0)
    self._http_class = functools.partial(
      HTTPSConnection,
      **connection_kw
    )

  def https_open(self, req):
    kw = {}
    if hasattr(self, '_context'): # BBB <= python 2.7.8
      kw['context'] = self._context
    return self.do_open(self._http_class, req, **kw)

# TODO: verify server's SSL certificate
class CaucaseRESTClientInterface(XMLObject):
  meta_type = 'Caucase REST Client Interface'
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)

  def _request(self, path, data=None, method=None):
    base_url = self.getUrlString()
    assert base_url.startswith('https://')
    url = urlparse.urljoin(base_url, path)
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, self.getUserId(), self.getPassword())
    request = urllib2.Request(
        url,
        data=data,
      )
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    request.add_header('Accept', 'text/plain')
    if method is not None:
      request.get_method = lambda: method
    # XXX to remove
    import ssl
    kw = {}
    if hasattr(ssl, '_create_unverified_context'):
      context = ssl._create_unverified_context()
      kw['context'] = context
    response = urllib2.build_opener(
      TolerateErrorHandler(),
      BoundHTTPSHandler(source_address=self.getSourceHostname(), **kw),
      urllib2.HTTPBasicAuthHandler(password_mgr),
    ).open(request,)
    if response.getcode() not in (200, 201, 204):
      raise ValueError('Server responded with status=%r, body=%r' % (
        response.getcode(),
        response.read(),
      ))
    return response

  def getCACertificate(self):
    """
      Get CA Certificate as PEM string
    """
    return self._request('crt/ca.crt.pem').read()

  def getCACertificateList(self):
    """
      Get CA Certificate as PEM string
    """
    return loads(self._request('/crt/ca.crt.json').read())

  def getCertificateFromSerial(self, serial):
    """
      Get Certificate as PEM string
    """
    return self._request('crt/serial/%s' % serial).read()

  def getCertificate(self, crt_id):
    """
      Get Certificate as PEM string
    """
    return self._request('crt/%s' % crt_id).read()

  def signCertificate(self, csr_id):
    """
      Sign a certificate from the CSR id
      
      return the certificate ID and URL to download certificate
    """
    data = urllib.urlencode({'csr_id': csr_id})
    response = self._request('/crt', data=data, method='PUT')
    cert_id = response.headers['Location'].split('/')[-1]
    return (cert_id, response.headers['Location'])

  def revokeCertificate(self, crt_id):
    """
      Revoke existing and valid certificate
    """
    return self._request(
      '/crt/revoke/id',
      data=urllib.urlencode({'crt_id': crt_id}),
      method='PUT'
    ).read()

  def getCertificateRevocationList(self):
    """
      Return the latest CRL in PEM string format
    """
    return self._request('/crl')

  def putCertificateSigningRequest(self, csr):
    """
      Send CSR signature to CA, return the csr key_id.
    """
    response = self._request(
      '/csr',
      data=urllib.urlencode({'csr': csr}),
      method='PUT'
    )
    return response.headers['Location'].split('/')[-1]

  def getCertificateSigningRequest(self, csr_id):
    """
      Return CSR from his id
    """
    return self._request('/csr/%s' % csr_id).read()

  def deleteCertificateSigningRequest(self, csr_id):
    """
      Return CSR from his id
    """
    response = self._request('/csr/%s' % csr_id, method='DELETE').read()
  
InitializeClass(CaucaseRESTClientInterface)