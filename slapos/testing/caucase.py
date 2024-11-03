# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2024 Nexedi and Contributors. All Rights Reserved.
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
# as published by the Free Software Foundation; either version 3
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

"""Utility classes to use caucase and certificates in tests."""

import hashlib
import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional
import urllib.parse

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import requests

from .utils import findFreeTCPPortRange, ManagedResource


class CaucaseService(ManagedResource):
  """A caucase service."""

  url: str
  directory: str
  _caucased_process: subprocess.Popen

  @property
  def ca_crt_path(self) -> str:
    """Path of the CA certificate from this caucase."""
    ca_crt_path = os.path.join(self.directory, "ca.crt.pem")
    if not os.path.exists(ca_crt_path):
      with open(ca_crt_path, "w") as f:
        f.write(
          requests.get(
            urllib.parse.urljoin(
              self.url,
              "/cas/crt/ca.crt.pem",
            )
          ).text
        )
    return ca_crt_path

  @property
  def _caucased_path(self) -> str:
    """path of caucased executable.

    Expects the software release to have `bin/caucased`
    """
    software_release_root_path = os.path.join(
      self._cls.slap._software_root,
      hashlib.md5(self._cls.getSoftwareURL().encode()).hexdigest(),
    )
    return os.path.join(software_release_root_path, "bin", "caucased")

  def open(self) -> None:
    # starts a caucased.
    self.directory = tempfile.mkdtemp()
    caucased_dir = os.path.join(self.directory, "caucased")
    os.mkdir(caucased_dir)
    os.mkdir(os.path.join(caucased_dir, "user"))
    os.mkdir(os.path.join(caucased_dir, "service"))

    backend_caucased_netloc = f"{self._cls._ipv4_address}:{findFreeTCPPortRange(self._cls._ipv4_address, 2)}"
    self.url = f"http://{backend_caucased_netloc}"
    self._caucased_process = subprocess.Popen(
      [
        self._caucased_path,
        "--db",
        os.path.join(caucased_dir, "caucase.sqlite"),
        "--server-key",
        os.path.join(caucased_dir, "server.key.pem"),
        "--netloc",
        backend_caucased_netloc,
        "--service-auto-approve-count",
        "1",
      ],
      # capture subprocess output not to pollute test's own stdout
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
    )
    for _ in range(30):
      try:
        if requests.get(self.url).ok:
          break
      except Exception:
        pass
      time.sleep(1)
    else:
      raise RuntimeError("caucased failed to start.")

  def close(self) -> None:
    self._caucased_process.terminate()
    self._caucased_process.wait()
    assert self._caucased_process.stdout
    self._caucased_process.stdout.close()
    shutil.rmtree(self.directory)


class CaucaseCertificate(ManagedResource):
  """A certificate signed by a caucase service."""

  ca_crt_file: str
  crl_file: str
  csr_file: str
  cert_file: str
  key_file: str

  def open(self) -> None:
    self.tmpdir = tempfile.mkdtemp()
    self.ca_crt_file = os.path.join(self.tmpdir, "ca-crt.pem")
    self.crl_file = os.path.join(self.tmpdir, "ca-crl.pem")
    self.csr_file = os.path.join(self.tmpdir, "csr.pem")
    self.cert_file = os.path.join(self.tmpdir, "crt.pem")
    self.key_file = os.path.join(self.tmpdir, "key.pem")

  def close(self) -> None:
    shutil.rmtree(self.tmpdir)

  @property
  def _caucase_path(self) -> str:
    """path of caucase executable."""
    software_release_root_path = os.path.join(
      self._cls.slap._software_root,
      hashlib.md5(self._cls.getSoftwareURL().encode()).hexdigest(),
    )
    return os.path.join(software_release_root_path, "bin", "caucase")

  def request(
    self,
    common_name: str,
    caucase: CaucaseService,
    san: Optional[x509.SubjectAlternativeName] = None,
  ) -> None:
    """Generate certificate and request signature to the caucase service.

    This overwrite any previously requested certificate for this instance.
    """
    cas_args = [
      self._caucase_path,
      "--ca-url",
      caucase.url,
      "--ca-crt",
      self.ca_crt_file,
      "--crl",
      self.crl_file,
    ]

    key = rsa.generate_private_key(
      public_exponent=65537, key_size=2048, backend=default_backend()
    )
    with open(self.key_file, "wb") as f:
      f.write(
        key.private_bytes(  # type:ignore
          encoding=serialization.Encoding.PEM,
          format=serialization.PrivateFormat.TraditionalOpenSSL,
          encryption_algorithm=serialization.NoEncryption(),
        )
      )

    csr = x509.CertificateSigningRequestBuilder().subject_name(
      x509.Name(
        [
          x509.NameAttribute(
            NameOID.COMMON_NAME,
            common_name,
          ),
        ]
      )
    )
    if san:
      csr = csr.add_extension(san, critical=True)
    csr = csr.sign(key, hashes.SHA256(), default_backend())
    with open(self.csr_file, "wb") as f:
      f.write(csr.public_bytes(serialization.Encoding.PEM))

    csr_id = (
      subprocess.check_output(
        cas_args
        + [
          "--send-csr",
          self.csr_file,
        ],
      )
      .split()[0]
      .decode()
    )
    assert csr_id

    for _ in range(30):
      if (
        not subprocess.call(
          cas_args
          + [
            "--get-crt",
            csr_id,
            self.cert_file,
          ],
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
        )
        == 0
      ):
        break
      else:
        time.sleep(1)
    else:
      raise RuntimeError("getting service certificate failed.")
    with open(self.cert_file) as cert_file:
      assert "BEGIN CERTIFICATE" in cert_file.read()

  def revoke(self, caucase: CaucaseService) -> None:
    """Revoke the client certificate on this caucase instance."""
    subprocess.check_call(
      [
        self._caucase_path,
        "--ca-url",
        caucase.url,
        "--ca-crt",
        self.ca_crt_file,
        "--crl",
        self.crl_file,
        "--revoke-crt",
        self.cert_file,
        self.key_file,
      ]
    )
