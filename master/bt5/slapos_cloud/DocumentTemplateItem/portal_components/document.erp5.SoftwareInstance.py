# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################
from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions
from erp5.component.document.Item import Item
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
