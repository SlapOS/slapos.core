from test_suite import SavedTestSuite, ProjectTestSuite
from glob import glob
import os, re
import sys

slapos_bt_list = [
    'erp5_web_shacache',
    'erp5_web_shadir',
    'slapos_accounting',
    'slapos_cache',
    'slapos_subscription_request',
    'slapos_cloud',
    'slapos_erp5',
    'slapos_pdm',
    'slapos_slap_tool',
    'slapos_web',
    'slapos_crm',
    'slapos_payzen',
    'slapos_wechat',
    'slapos_configurator',
    'slapos_jio',
    'slapos_jio_ui_test'
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
      elif test_path.split(os.sep)[-3] == 'Vifib':
        # There is no valid tests in Vifib!
        continue
      test_list.append(test_case)
    return test_list

  def run(self, full_test):
    test = ':' in full_test and full_test.split(':')[1] or full_test
    if test.startswith('testFunctional'):
      return self._updateFunctionalTestResponse(self.runUnitTest(full_test))
    return super(SlapOSCloud, self).run(full_test)

  def _updateFunctionalTestResponse(self, status_dict):
    """ Convert the Unit Test output into more accurate information
        related to funcional test run.
    """
    # Parse relevant information to update response information
    try:
      summary, html_test_result = status_dict['stderr'].split("-"*79)[1:3]
    except ValueError:
      # In case of error when parse the file, preserve the original
      # informations. This prevents we have unfinished tests.
      return status_dict
    status_dict['html_test_result'] = html_test_result
    search = self.FTEST_PASS_FAIL_RE.search(summary)
    if search:
      group_dict = search.groupdict()
      status_dict['failure_count'] = int(group_dict['failures'])
      status_dict['test_count'] = int(group_dict['total'])
      status_dict['skip_count'] = int(group_dict['expected_failure'])
    return status_dict
