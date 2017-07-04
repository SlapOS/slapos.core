# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Nexedi SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions
from Products.ERP5.Document.Item import Item
from lxml import etree
import collections

class DisconnectedSoftwareTree(Exception):
  pass

class CyclicSoftwareTree(Exception):
  pass

class SoftwareInstance(Item):
  """
  """

  meta_type = 'ERP5 Software Instance'
  portal_type = 'Software Instance'
  add_permission = Permissions.AddPortalContent

  # Declarative security
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)


  def _getXmlAsDict(self, xml):
    result_dict = {}
    if xml is None or xml == '':
      return result_dict

    tree = etree.fromstring(xml)

    for element in tree.findall('parameter'):
      key = element.get('id').encode("UTF-8")
      value = result_dict.get(key, None)
      if value is not None:
        value = (value + ' ' + element.text)
      else:
        value = element.text
      if value is not None:
        value = value.encode("UTF-8")
      result_dict[key] = value
    return result_dict

  def _getInstanceCertificate(self):
    certificate_id_list = [x for x in
      self.contentValues(portal_type="Certificate Access ID")
      if x.getValidationState() == 'validated']

    if certificate_id_list:
      return certificate_id_list[0]

  def _getCertificate(self, cert_id):
    return self.getPortalObject().portal_web_services.caucase_adapter\
        .getCertificate(cert_id)

  security.declareProtected(Permissions.AccessContentsInformation,
    'getCertificate')
  def getCertificate(self):
    """Returns existing certificate of this instance"""
    certificate_id = self._getInstanceCertificate()
    if certificate_id:
      return self._getCertificate(certificate_id.getReference())
    raise ValueError(
      "No certificate set for Software Instance %s" % self.getReference()
    )

  security.declareProtected(Permissions.AccessContentsInformation,
    'requestCertificate')
  def requestCertificate(self, certificate_request):
    """Request a new certificate for this instance"""
    certificate_id = self._getInstanceCertificate()
    if certificate_id is not None:
      # Get new Certificate will automatically revoke the previous
      self.revokeCertificate(certificate_id=certificate_id)

    ca_service = self.getPortalObject().portal_web_services.caucase_adapter
    csr_id = ca_service.putCertificateSigningRequest(certificate_request)

    # Sign the csr immediately
    crt_id, url = ca_service.signCertificate(
      csr_id,
      subject={'CN': self.getReference()}
    )

    # link to the Instance
    certificate_id = self.newContent(
      portal_type="Certificate Access ID",
      reference=crt_id,
      url_string=url)

    certificate_id.validate()
    return self._getCertificate(certificate_id.getReference())

  security.declareProtected(Permissions.AccessContentsInformation,
    'revokeCertificate')
  def revokeCertificate(self, certificate_id=None):
    """Revoke existing certificate of this instance"""
    if certificate_id is None:
      certificate_id = self._getInstanceCertificate()
    if certificate_id:
      self.getPortalObject().portal_web_services.caucase_adapter \
          .revokeCertificate(certificate_id.getReference())
      certificate_id.invalidate()
    else:
      raise ValueError(
        "No certificate found for Software Instance %s" % self.getReference()
      )

  security.declareProtected(Permissions.AccessContentsInformation,
    'getSlaXmlAsDict')
  def getSlaXmlAsDict(self):
    """Returns SLA XML as python dictionary"""
    return self._getXmlAsDict(self.getSlaXml())

  security.declareProtected(Permissions.AccessContentsInformation,
    'getInstanceXmlAsDict')
  def getInstanceXmlAsDict(self):
    """Returns Instance XML as python dictionary"""
    return self._getXmlAsDict(self.getTextContent())

  security.declareProtected(Permissions.AccessContentsInformation,
    'getConnectionXmlAsDict')
  def getConnectionXmlAsDict(self):
    """Returns Connection XML as python dictionary"""
    return self._getXmlAsDict(self.getConnectionXml())

  security.declareProtected(Permissions.AccessContentsInformation,
    'checkNotCyclic')
  def checkNotCyclic(self, graph):
    # see http://neopythonic.blogspot.com/2009/01/detecting-cycles-in-directed-graph.html
    todo = set(graph.keys())
    while todo:
      node = todo.pop()
      stack = [node]
      while stack:
        top = stack[-1]
        for node in graph[top]:
          if node in stack:
            raise CyclicSoftwareTree
          if node in todo:
            stack.append(node)
            todo.remove(node)
            break
        else:
          node = stack.pop()
    return True

  security.declareProtected(Permissions.AccessContentsInformation,
    'checkConnected')
  def checkConnected(self, graph, root):
    size = len(graph)
    visited = set()
    to_crawl = collections.deque(graph[root])
    while to_crawl:
      current = to_crawl.popleft()
      if current in visited:
        continue
      visited.add(current)
      node_children = set(graph[current])
      to_crawl.extend(node_children - visited)
    # add one to visited, as root won't be visited, only children
    # this is false positive in case of cyclic graphs, but they are
    # anyway wrong in Software Instance trees
    if size != len(visited) + 1:
      raise DisconnectedSoftwareTree
    return True
