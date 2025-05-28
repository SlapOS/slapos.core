from test_suite import SavedTestSuite, ProjectTestSuite
from glob import glob
import os, re
import sys

slapos_bt_list = [
    'erp5_web_shacache',
    'erp5_web_shadir',
    'slapos_accounting',
    'slapos_subscription_request',
    'slapos_cloud',
    'slapos_erp5',
    'slapos_pdm',
    'slapos_slap_tool',
    'slapos_crm',
    'slapos_payzen',
    'slapos_wechat',
    'slapos_configurator',
    'slapos_mysql_innodb_catalog',
    'slapos_panel_ui_test',
    'slapos_parameter_editor_ui_test',
    'slapos_abyss',
    'slapos_rss_style',
    'slapos_json_rpc_api',
  ]

class SlapOSCloud(SavedTestSuite, ProjectTestSuite):
  _product_list = ['SlapOS']
  _saved_test_id = 'Products.SlapOS.tests.testSlapOSMixin.testSlapOSMixin'
  _bt_list = slapos_bt_list

  def getTestList(self):
    test_list = []
    path = sys.path[0]
    erp5_path = sys.path[1]
    component_re = re.compile(".*/([^/]+)/TestTemplateItem/portal_components"
                              "/test\.[^.]+\.([^.]+).py$")
    for test_path in (
        glob('%s/product/*/tests/test*.py' % path) +
        glob('%s/bt5/*/TestTemplateItem/test*.py' % path) +
        glob('%s/bt5/*/TestTemplateItem/portal_components/test.*.test*.py' % path) +
        glob('%s/bt5/*/TestTemplateItem/test*.py' % erp5_path) +
        glob('%s/bt5/*/TestTemplateItem/portal_components/test.*.test*.py' % erp5_path)):
      component_re_match = component_re.match(test_path)
      if component_re_match is not None:
        test_case = "%s:%s" % (component_re_match.group(1),
                               component_re_match.group(2))
      else:
        test_case = test_path.split(os.sep)[-1][:-3] # remove .py
      # Filter bt tests to run from _bt_list list
      if test_path.split(os.sep)[-2] != 'tests':
        if test_path.split(os.sep)[-2] == 'portal_components':
          product = test_path.split(os.sep)[-4]
        else:
          product = test_path.split(os.sep)[-3]
        if not product in self._bt_list:
          continue
      test_list.append(test_case)
    return test_list

  def run(self, full_test):
    test = ':' in full_test and full_test.split(':')[1] or full_test
    if test in ('testSlapOSWendelinCoreTwo', 'testSlapOSAbyss'):
      return self.runUnitTest('--with_wendelin_core', '--activity_node=1', full_test)
    elif test.startswith('testFunctional'):
      return self._updateFunctionalTestResponse(self.runUnitTest(full_test))
    elif test.startswith('testSlapOSMixin'):
      return ProjectTestSuite.runUnitTest(self,
         '--portal_id=erp5',
         '--enable_full_indexing=portal_types,portal_property_sheets',
         full_test)
    return super(SlapOSCloud, self).run(full_test)

  def _updateFunctionalTestResponse(self, status_dict):
    """ Convert the Unit Test output into more accurate information
        related to functional test run.
    """
    # Parse relevant information to update response information
    try:
      summary, html_test_result = status_dict['stderr'].split(b"-"*79)[1:3]
    except ValueError:
      # In case of error when parse the file, preserve the original
      # information. This prevents we have unfinished tests.
      return status_dict
    status_dict['html_test_result'] = html_test_result
    search = self.FTEST_PASS_FAIL_RE.search(summary.decode())
    if search:
      group_dict = search.groupdict()
      status_dict['failure_count'] = int(group_dict['failures']) \
          or int(status_dict.get('failure_count', 0))
      status_dict['test_count'] = int(group_dict['total'])
      status_dict['skip_count'] = int(group_dict['expected_failure'])
    return status_dict


class SlapOSDocTestSuite(SlapOSCloud):
  _product_list = []
  _saved_test_id = 'erp5_slapos_tutorial:testFunctionalStandaloneSlapOSTutorial'
  _bt_list = ['erp5_slapos_tutorial']

  def getTestList(self):
    test_list = []
    path = sys.path[0]
    erp5_doc_path = sys.path[1]
    component_re = re.compile(".*/([^/]+)/TestTemplateItem/portal_components"
                              "/test\.[^.]+\.([^.]+).py$")
    for test_path in (
        glob('%s/bt5/*/TestTemplateItem/portal_components/test.*.test*.py' % erp5_doc_path)):
      component_re_match = component_re.match(test_path)
      if component_re_match is not None:
        test_case = "%s:%s" % (component_re_match.group(1),
                               component_re_match.group(2))
      else:
        test_case = test_path.split(os.sep)[-1][:-3] # remove .py
      test_list.append(test_case)
    return test_list
