##############################################################################
#
# Copyright (c) 2013 Vifib SARL and Contributors. All Rights Reserved.
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
import functools
import json
import logging
import os
import shutil
import tempfile
import textwrap
import unittest
from pwd import getpwnam

from six.moves import SimpleHTTPServer
import jsonschema

import slapos.util
from slapos.slap.slap import DEFAULT_SOFTWARE_TYPE
from slapos.testing.utils import ManagedHTTPServer
from slapos.util import (SoftwareReleaseSchema, SoftwareReleaseSerialisation,
                         string_to_boolean, unicode2str)


class TestUtil(unittest.TestCase):
  """
  Tests methods available in the slapos.util module.
  """

  def test_mkdir_p_new_directory(self):
    """
    Test that mkdir_p recursively creates a directory.
    """
    root_directory = tempfile.mkdtemp()
    wanted_directory = os.path.join(root_directory, 'foo', 'bar')
    slapos.util.mkdir_p(wanted_directory)
    self.assertTrue(os.path.isdir(wanted_directory))
    shutil.rmtree(root_directory)

  def test_mkdir_already_existing(self):
    """
    Check that mkdir_p doesn't raise if directory already exist.
    """
    root_directory = tempfile.mkdtemp()
    slapos.util.mkdir_p(root_directory)
    self.assertTrue(os.path.isdir(root_directory))
    shutil.rmtree(root_directory)

  def test_chown_directory(self):
    """
    Test that slapos.util.chownDirectory correctly changes owner.
    Note: requires root privileges.
    """
    root_slaptest = tempfile.mkdtemp()
    wanted_directory0 = os.path.join(root_slaptest, 'slap-write0')
    wanted_directory1 = os.path.join(root_slaptest, 'slap-write0', 'write-slap1')
    wanted_directory2 = os.path.join(root_slaptest, 'slap-write0', 'write-slap1', 'write-teste2')
    wanted_directory_mkdir0 = os.makedirs(wanted_directory0, mode=0o777)
    wanted_directory_mkdir1 = os.makedirs(wanted_directory1, mode=0o777)
    wanted_directory_mkdir2 = os.makedirs(wanted_directory2, mode=0o777)
    create_file_txt = tempfile.mkstemp(suffix='.txt', prefix='tmp', dir=wanted_directory2, text=True)
    user = 'nobody'
    try:
      uid = getpwnam(user)[2]
      gid = getpwnam(user)[3]
    except KeyError:
      raise unittest.SkipTest("user %s doesn't exist." % user)

    if os.getuid() != 0:
      raise unittest.SkipTest("No root privileges, impossible to chown.")

    slapos.util.chownDirectory(root_slaptest, uid, gid)

    uid_check_root_slaptest = os.stat(root_slaptest)[4]
    gid_check_root_slaptest = os.stat(root_slaptest)[5]
    self.assertEqual(uid, uid_check_root_slaptest)
    self.assertEqual(gid, gid_check_root_slaptest)

    uid_check_wanted_directory0 = os.stat(wanted_directory0)[4]
    gid_check_wanted_directory0 = os.stat(wanted_directory0)[5]
    self.assertEqual(uid, uid_check_wanted_directory0)
    self.assertEqual(gid, gid_check_wanted_directory0)

    uid_check_wanted_directory1 = os.stat(wanted_directory1)[4]
    gid_check_wanted_directory1 = os.stat(wanted_directory1)[5]
    self.assertEqual(uid, uid_check_wanted_directory1)
    self.assertEqual(gid, gid_check_wanted_directory1)

    uid_check_wanted_directory2 = os.stat(wanted_directory2)[4]
    gid_check_wanted_directory2 = os.stat(wanted_directory2)[5]
    self.assertEqual(uid,  uid_check_wanted_directory2)
    self.assertEqual(gid, gid_check_wanted_directory2)

    uid_check_file_txt = os.stat(create_file_txt[1])[4]
    gid_check_file_txt = os.stat(create_file_txt[1])[5]
    self.assertEqual(uid, uid_check_file_txt)
    self.assertEqual(gid, gid_check_file_txt)

    shutil.rmtree(root_slaptest)

  def test_string_to_boolean_with_true_values(self):
    for value in ['true', 'True', 'TRUE']:
      self.assertTrue(string_to_boolean(value))

  def test_string_to_boolean_with_false_values(self):
    for value in ['false', 'False', 'False']:
      self.assertFalse(string_to_boolean(value))

  def test_string_to_boolean_with_incorrect_values(self):
    for value in [True, False, 1, '1', 't', 'tru', 'truelle', 'f', 'fals', 'falsey']:
      self.assertRaises(ValueError, string_to_boolean, value)

  xml2dict0_xml = slapos.util.bytes2str(b"""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="badstr">\xc5\x81</parameter>
  <parameter id="badu">\xc5\x81</parameter>
  <parameter id="emptystr"></parameter>
  <parameter id="int">1</parameter>
  <parameter id="intstr">1</parameter>
  <parameter id="key">str</parameter>
  <parameter id="list">['one', 2]</parameter>
  <parameter id="none">None</parameter>
  <parameter id="ukey">ustr</parameter>
</instance>
""")

  xml2dict0_indict = {
    u'ukey': u'ustr',
    'key': 'str',
    'int': 1,
    'intstr': '1',
    'emptystr': '',
    'none': None,
    'list': ['one', 2],
    'badstr': u'\u0141'.encode('utf-8'),
    'badu': u'\u0141'
  }

  xml2dict0_outdict = {
    'badstr': u'\u0141',
    'badu': u'\u0141',
    'emptystr': None,
    'int': '1',
    'intstr': '1',
    'key': 'str',
    'list': "['one', 2]",
    'none': 'None',
    'ukey': 'ustr'}

  def test_xml2dict0(self):
    self.assertEqual(
      dict,
      type(slapos.util.xml2dict(self.xml2dict0_xml))
    )
    self.assertEqual(
      self.xml2dict0_outdict,
      slapos.util.xml2dict(self.xml2dict0_xml)
    )

  def test_dict2xml0(self):
    self.maxDiff = None
    self.assertEqual(
      self.xml2dict0_xml,
      slapos.util.dict2xml(self.xml2dict0_indict)
    )


  xml2dict1_xml = """<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="_">{
    "param1": "value1",
    "param2_dict": {
        "param2_param1": "",
        "param2_param2_dict": {},
        "param2_param3_dict": {
            "param": "value"
        }
    }
}</parameter>
</instance>
"""

  xml2dict1_dict = {
    "_": '''{
    "param1": "value1",
    "param2_dict": {
        "param2_param1": "",
        "param2_param2_dict": {},
        "param2_param3_dict": {
            "param": "value"
        }
    }
}'''
  }

  def test_xml2dict1(self):
    self.maxDiff = None
    self.assertEqual(
      self.xml2dict1_dict,
      slapos.util.xml2dict(self.xml2dict1_xml)
    )

  def test_dict2xml1(self):
    self.maxDiff = None
    self.assertEqual(
      self.xml2dict1_xml,
      slapos.util.dict2xml(self.xml2dict1_dict)
    )

  def test_dumps_loads(self):
    simple_object = {"ok": [True]}
    self.assertEqual(simple_object, slapos.util.loads(slapos.util.dumps(simple_object)))

    self.assertRaises(
        Exception,
        slapos.util.loads,
            b'<marshal><object id="i2" module="nasty" class="klass">'
            b'<tuple></tuple><dictionary id="i3"/></object></marshal>')

    class Nasty(object):
      pass
    self.assertRaises(Exception, slapos.util.dumps, Nasty())


class SoftwareReleaseSchemaTestXmlSerialisationMixin:
  serialisation = SoftwareReleaseSerialisation.Xml
  serialisation_alt = SoftwareReleaseSerialisation.JsonInXml


class SoftwareReleaseSchemaTestJsonInXmlSerialisationMixin:
  serialisation = SoftwareReleaseSerialisation.JsonInXml
  serialisation_alt = SoftwareReleaseSerialisation.Xml


class SoftwareReleaseSchemaTestMixin(object):
  """Mixin with test methods
  """
  software_url = None # type: str
  serialisation = None # type: SoftwareReleaseSerialisation
  serialisation_alt = None # type: SoftwareReleaseSerialisation


  def test_software_schema(self):
    schema = SoftwareReleaseSchema(self.software_url, None)
    software_schema = schema.getSoftwareSchema()
    self.assertEqual(software_schema['name'], 'Test Software')
    self.assertEqual(len(software_schema['software-type']), 2)

  def test_serialisation(self):
    schema = SoftwareReleaseSchema(self.software_url, None)
    self.assertEqual(schema.getSerialisation(), self.serialisation)

  def test_serialisation_alternate_software_type(self):
    schema = SoftwareReleaseSchema(self.software_url, 'alternate')
    self.assertEqual(schema.getSerialisation(), self.serialisation_alt)

  def test_instance_request_parameter_schema_default_software_type(self):
    schema = SoftwareReleaseSchema(self.software_url, None)
    self.assertTrue(schema.getInstanceRequestParameterSchemaURL())
    instance_parameter_schema = schema.getInstanceRequestParameterSchema()
    self.assertEqual(instance_parameter_schema['description'],
                     "Simple instance parameters schema for tests")

  def test_connection_parameter_schema(self):
    schema = SoftwareReleaseSchema(self.software_url, None)
    self.assertTrue(schema.getInstanceConnectionParameterSchemaURL())
    instance_parameter_schema = schema.getInstanceConnectionParameterSchema()
    self.assertEqual(instance_parameter_schema['description'],
                     "Simple connection parameters schema for tests")

  def test_instance_request_parameter_validate_default_software_type(self):
    schema = SoftwareReleaseSchema(self.software_url, None)
    self.assertTrue(schema.getInstanceRequestParameterSchemaURL())
    instance_ok = {'key': 'value', 'type': 'default'}
    schema.validateInstanceParameterDict(instance_ok)

    if self.serialisation == SoftwareReleaseSerialisation.JsonInXml:
      # already serialized values are also tolerated
      schema.validateInstanceParameterDict({'_': json.dumps(instance_ok)})

    with self.assertRaises(jsonschema.ValidationError):
      schema.validateInstanceParameterDict({"wrong": True})
    instance_ok['key'] = False # wrong type
    with self.assertRaises(jsonschema.ValidationError):
      schema.validateInstanceParameterDict(instance_ok)
    with self.assertRaises(jsonschema.ValidationError):
      schema.validateInstanceParameterDict({'_': json.dumps(instance_ok)})

  def test_instance_request_parameter_validate_alternate_software_type(self):
    schema = SoftwareReleaseSchema(self.software_url, 'alternate')
    self.assertTrue(schema.getInstanceRequestParameterSchemaURL())
    instance_ok = {'key': 'value', 'type': 'alternate'}
    schema.validateInstanceParameterDict(instance_ok)

    if self.serialisation_alt == SoftwareReleaseSerialisation.JsonInXml:
      # already serialized values are also tolerated
      schema.validateInstanceParameterDict({'_': json.dumps(instance_ok)})

    with self.assertRaises(jsonschema.ValidationError):
      schema.validateInstanceParameterDict({"wrong": True})
    instance_ok['type'] = 'wrong'
    with self.assertRaises(jsonschema.ValidationError):
      schema.validateInstanceParameterDict(instance_ok)
    with self.assertRaises(jsonschema.ValidationError):
      schema.validateInstanceParameterDict({'_': json.dumps(instance_ok)})

  def test_instance_request_parameter_schema_alternate_software_type(self):
    schema = SoftwareReleaseSchema(self.software_url, 'alternate')
    self.assertTrue(schema.getInstanceRequestParameterSchemaURL())
    instance_parameter_schema = schema.getInstanceRequestParameterSchema()
    self.assertEqual(instance_parameter_schema['description'],
                     "Simple instance parameters schema for tests")


class SoftwareReleaseSchemaTestFileSoftwareReleaseMixin(SoftwareReleaseSchemaTestMixin):
  """Mixin with tests and software release profiles and schema in a
  temporary directory.
  """
  def setUp(self):
    self.tmpdir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, self.tmpdir)
    tmpfile = functools.partial(os.path.join, self.tmpdir)
    with open(tmpfile('software.cfg'), 'w') as f:
      f.write(
        textwrap.dedent("""\
          [buildout]
          """))
    with open(tmpfile('software.cfg.json'), 'w') as f:
      json.dump(
          {
              "name": "Test Software",
              "description": "Dummy software for Test",
              "serialisation": self.serialisation,
              "software-type": {
                  DEFAULT_SOFTWARE_TYPE: {
                      "title": "Default",
                      "description": "Default type",
                      "request": "instance-default-input-schema.json",
                      "response": "instance-default-output-schema.json",
                      "index": 0
                  },
                  "alternate": {
                      "title": "Alternate",
                      "description": "Alternate type",
                      "serialisation": self.serialisation_alt,
                      "request": "instance-alternate-input-schema.json",
                      "response": "instance-alternate-output-schema.json",
                      "index": 0
                  },
              }
          }, f)

    for software_type in ('default', 'alternate'):
      with open(
          tmpfile('instance-{software_type}-input-schema.json'.format(
              software_type=software_type)), 'w') as f:
        json.dump(
            {
                "$schema": "http://json-schema.org/draft-07/schema",
                "description": "Simple instance parameters schema for tests",
                "required": ["key", "type"],
                "properties": {
                    "key": {
                        "$ref": "./schemas-definitions.json#/key"
                    },
                    "type": {
                        "type": "string",
                        "const": software_type
                    }
                },
                "type": "object"
            }, f)
      with open(
          tmpfile('instance-{software_type}-output-schema.json'.format(
              software_type=software_type)), 'w') as f:
        json.dump(
            {
                "$schema": "http://json-schema.org/draft-07/schema",
                "description": "Simple connection parameters schema for tests",
            }, f)

    with open(tmpfile('schemas-definitions.json'), 'w') as f:
      json.dump({"key": {"type": "string"}}, f)

    self.software_url = tmpfile('software.cfg')


class SoftwareReleaseSchemaTestHTTPSoftwareReleaseMixin(SoftwareReleaseSchemaTestFileSoftwareReleaseMixin):
  """Mixin serving software release files over http.
  """
  def setUp(self):
    super(SoftwareReleaseSchemaTestHTTPSoftwareReleaseMixin, self).setUp()

    class ProfileHTTPServer(ManagedHTTPServer):
      hostname = os.environ['SLAPOS_TEST_IPV4']
      working_directory = self.tmpdir
      RequestHandler = SimpleHTTPServer.SimpleHTTPRequestHandler

    self.logger = logging.getLogger(self.id())
    self.logger.propagate = False

    server = ProfileHTTPServer(self, 'server')
    server.open()
    self.addCleanup(server.close)

    self.software_url = server.url + '/software.cfg'


class TestSoftwareReleaseSchemaFileSoftwareReleaseXmlSerialisation(
    SoftwareReleaseSchemaTestXmlSerialisationMixin,
    SoftwareReleaseSchemaTestFileSoftwareReleaseMixin,
    unittest.TestCase):
  pass


class TestSoftwareReleaseSchemaFileSoftwareReleaseJsonInXmlSerialisation(
    SoftwareReleaseSchemaTestJsonInXmlSerialisationMixin,
    SoftwareReleaseSchemaTestFileSoftwareReleaseMixin,
    unittest.TestCase):
  pass


class TestSoftwareReleaseSchemaHTTPSoftwareReleaseXmlSerialisation(
    SoftwareReleaseSchemaTestXmlSerialisationMixin,
    SoftwareReleaseSchemaTestHTTPSoftwareReleaseMixin,
    unittest.TestCase):
  pass


class TestSoftwareReleaseSchemaHTTPSoftwareReleaseJsonInXmlSerialisation(
    SoftwareReleaseSchemaTestJsonInXmlSerialisationMixin,
    SoftwareReleaseSchemaTestHTTPSoftwareReleaseMixin,
    unittest.TestCase):
  pass



class TestSoftwareReleaseSchemaEdgeCases(unittest.TestCase):

  def test_software_schema_file_not_exist(self):
    schema = SoftwareReleaseSchema('/file/not/exist', None)
    self.assertIsNone(schema.getSoftwareSchema())

  def test_software_schema_wrong_URL(self):
    schema = SoftwareReleaseSchema('http://slapos.invalid/software.cfg', None)
    self.assertIsNone(schema.getSoftwareSchema())


if __name__ == '__main__':
  unittest.main()
