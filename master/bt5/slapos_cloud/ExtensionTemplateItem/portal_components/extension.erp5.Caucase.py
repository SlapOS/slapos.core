###############################################################################
#
# Copyright (c) 2002-2011 Nexedi SA and Contributors. All Rights Reserved.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################

from urlparse import urlparse, urljoin
import ssl
import string
import random
import urllib2
import urllib


def generatePassword():
  return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))

def getCaucaseUrl(promise_url):
  parse_url = urlparse(promise_url)
  if parse_url.scheme == 'http':
    if parse_url.port:
      # Always consider caucase https port is http port + 1
      https_port = parse_url.port + 1
      port_index = parse_url.netloc.rindex('%s' % parse_url.port)
      return (parse_url.hostname,
              'https://%s%s/%s' % (parse_url.netloc[:port_index], https_port, parse_url.path))
    else:
      return (parse_url.hostname,
              'https://%s%s' % (parse_url.netloc, parse_url.path))
  else:
    return parse_url.hostname, promise_url

def getCaucaseServiceUrl(self, promise_url):
  return getCaucaseUrl(promise_url)

def configureCaucase(self, promise_url):
  if not promise_url:
    return

  ca_service = self.getPortalObject().portal_web_services.caucase_adapter
  hostname, caucase_url = getCaucaseUrl(promise_url)

  # XXX - we should create a valid ssl context from caucase
  context = ssl._create_unverified_context()
  response = urllib2.urlopen(caucase_url, context=context)

  if response.getcode() != 200:
    raise ValueError('Server responded with status=%r, url=%r, body=%r' % (
      response.getcode(),
      caucase_url,
      response.read(),
    ))

  if response.geturl().endswith('admin/configure'):
    # no password set, we where redirected to set password page
    # set a new password
    password = generatePassword()
    passwd_url = urljoin(caucase_url, '/admin/setpassword')
    request_dict = {'password': password}
    request = urllib2.Request(passwd_url, urllib.urlencode(request_dict))
    response = urllib2.urlopen(request, context=context)
    if response.getcode() != 200:
      raise ValueError('Server responded with status=%r, url=%r, body=%r' % (
        response.getcode(),
        passwd_url,
        response.read(),
      ))

    ca_service.edit(source_hostname=hostname,
                    url_string=caucase_url,
                    user_id='admin',
                    password=password)
  else:
    ca_service.edit(source_hostname=hostname,
                    url_string=caucase_url)
  if ca_service.getValidationState() != 'validated':
    ca_service.validate()
