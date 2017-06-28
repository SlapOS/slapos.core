# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import errno
import os
import subprocess
import sqlite3
import re
from OpenSSL import crypto, SSL
from datetime import datetime, timedelta


def parse_certificate_from_html(html):
  """
  Extract certificate from an HTML page received by SlapOS Master.
  """

  regex = r"(-{5}BEGIN\sCERTIFICATE-{5}.*-{5}END\sCERTIFICATE-{5})"
  result = re.search(regex, html, re.DOTALL)
  if result:
    return result.groups()[0]

  return certificate

def generateCertificateRequest(key_string, cn,
    country='', state='', locality='', email='', organization='',
    organization_unit='', csr_file=None, digest="sha256"):
  """
    Generate certificate Signature request.
    
    Parameter `cn` is mandatory
  """

  key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_string)

  req = crypto.X509Req()
  subject = req.get_subject()
  subject.CN = cn
  if country:
    subject.C = country
  if state:
    subject.ST = state
  if locality:
    subject.L = locality
  if organization:
    subject.O = organization
  if organization_unit:
    subject.OU = organization_unit
  if email:
    subject.emailAddress = email
  req.set_pubkey(key)
  req.add_extensions([
      crypto.X509Extension("basicConstraints", False, "CA:FALSE"),
      crypto.X509Extension("keyUsage", False,
        "nonRepudiation, digitalSignature, keyEncipherment")
    ])
  req.sign(key, digest)

  csr = crypto.dump_certificate_request(crypto.FILETYPE_PEM, req)

  if csr_file is not None:
    with open(csr_file, 'w') as req_file:
      req_file.write(csr)

    os.chmod(csr_file, 0640)

  return csr

def generatePkey(size=2048):
  key = crypto.PKey()
  key.generate_key(crypto.TYPE_RSA, size)
  return crypto.dump_privatekey(crypto.FILETYPE_PEM, key)

def generatePrivatekey(key_file, size=2048, uid=None, gid=None):
  """
    Generate private key into `key_file` and return the pkey string
  """

  try:
    key_fd = os.open(key_file,
                     os.O_CREAT|os.O_WRONLY|os.O_EXCL|os.O_TRUNC,
                     0600)
  except OSError, e:
    if e.errno != errno.EEXIST:
      raise
    # return existing certificate content
    return open(key_file).read()
  else:
    pkey = generatePkey(size)
    os.write(key_fd, pkey)
    os.close(key_fd)
    if uid and gid:
      os.chown(key_file, uid, gid)
    return pkey


def validateCertAndKey(cert_file, key_file):
  with open(cert_file) as ct:
    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, ct.read())
  with open(key_file) as kf:
    key = crypto.load_privatekey(crypto.FILETYPE_PEM, kf.read())

  ctx = SSL.Context(SSL.TLSv1_METHOD)
  ctx.use_privatekey(key)
  ctx.use_certificate(x509)
  ctx.check_privatekey()
