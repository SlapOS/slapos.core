# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2013-2019  Nexedi SA and Contributors.
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

from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixin
import os


class TestSlapOSConfigurator(SlapOSTestCaseMixin):

  maxDiff = None
  def testConfiguredModuleGeneratorIDViaConstraint(self):
    """ Make sure Generator ID is well configured, in this
        case we trust on promise outcome."""
    self.assertEqual(self.portal.portal_ids.checkConsistency(), [])

    self.portal.person_module.setIdGenerator("_Id_fake")
    self.assertNotEqual(self.portal.portal_ids.checkConsistency(), [])
    self.portal.portal_ids.fixConsistency()
    self.assertEqual(self.portal.portal_ids.checkConsistency(), [])
    self.assertEqual(self.portal.person_module.getIdGenerator(),
                        "_generatePerDayNodeNumberId")

  def testConfiguredShacacheWebSite(self):
    """ Make sure Shacache WebSite is setuped by Alarm
        case we trust on promise outcome, this checks:
        WebSiteModule_checkShacacheConstraint """
    self.assertEqual(self.portal.web_site_module.checkConsistency(), [])

  def testConfiguredCacheViaConstraint(self):
    """ Make sure Volitile and Persistent Cache was configured well,
        invoking the consistency to check """
    self.assertEqual(self.portal.portal_memcached.checkConsistency(), [])

  def testConfiguredConversionServerViaConstraint(self):
    """ Make sure Conversion Server was configured well,
        invoking checkConsistency """
    pref_tool = self.portal.portal_preferences
    self.portal.portal_preferences.fixConsistency()
    consistency_list = pref_tool.checkConsistency()
    # It is not recursive anymore
    self.assertEqual(len(consistency_list), 0)

    pref_tool.getActiveSystemPreference().fixConsistency()
    pref_tool.slapos_default_system_preference.fixConsistency()
    self.tic()
    self.assertEqual(
        pref_tool.getActiveSystemPreference().getId(),
        'slapos_default_system_preference'
    )

    consistency_list = pref_tool.getActiveSystemPreference().checkConsistency()
    # It is not recursive anymore
    self.assertEqual(len(consistency_list), 1)
    self.assertEqual(str(consistency_list[0].message),
      'The System Preference subscription assignment should have a destination_project')

    # Check if configuration is properly set:
    consistency_list = pref_tool.slapos_default_system_preference.SystemPreference_checkSystemPreferenceConsistency()
    self.assertEqual(len(consistency_list), 1)
    self.assertEqual(str(consistency_list[0]),
      'The System Preference subscription assignment should have a destination_project')

  def testConfiguredCertificateAuthoringConstraint(self):
    """Make sure Certificate Authoring was configured well,
       invoking checkConsistency.

       Make sure PAS is well configured."""
    # The certificate_authority_path is modified by the setup, invoke
    # fixConsistency here to restore it like the originally expected.    
    self.portal.portal_certificate_authority.fixConsistency()

    self.assertEqual(self.portal.portal_certificate_authority.checkConsistency(), [])

  def testConfiguredTemplateToolViaConstraint(self):
    """ Make sure Template Tool Repositories was configured well,
        invoking checkConsistency """
    self.assertEqual(
        [ i for i in self.portal.portal_templates.checkConsistency()
                     if not ("(reinstall)" in i.message or "Update translation table" in i.message)], [])

  def testConfiguredModuleBusinessApplication(self):
    """ Make sure that Modules has proper business_application set
        by TemplateToolBusinessApplicationModuleCategoryConstraint constraint """
    
    self.assertEqual([],
      self.portal.portal_templates.TemplateTool_checkBusinessApplicationToModuleConsistency())

  def test_SystemPreference_checkConversionServerConsistency(self):
    """ Make sure Conversion Server (Cloudooo) is
        well configured."""
    # set preference
    preference_tool = self.portal.portal_preferences
    conversion_url = ["https://cloudooo.erp5.net/",
                      "https://cloudooo1.erp5.net/"]
    self.assertSameSet(preference_tool.getPreferredDocumentConversionServerUrlList(), conversion_url)

  def testConfiguredCertificateAuthoring(self):
    """ Make sure Certificate Authoting is
        well configured. """

    if self.isLiveTest():
      # This test is redundant with testConfiguredVolatileCacheViaPromise
      # and it is only aims to verify if test environment is behaving as
      # expected, nothing else, and if alamrs were invoked.
      return

    # The certificate_authority_path is modified by the setup, invoke
    # fixConsistency here to restore it like the originally expected.
    self.portal.portal_certificate_authority.fixConsistency()

    self.assertTrue(self.portal.hasObject('portal_certificate_authority'))
    self.assertEqual(os.environ['TEST_CA_PATH'],
          self.portal.portal_certificate_authority.certificate_authority_path)

  def testAlarmIsSubscribed(self):
    """ Make sure portal_alarms is subscribed. """
    self.assertTrue(self.portal.portal_alarms.isSubscribed())

  def test_TemplateTool_checkSlapOSPASConsistency(self):
    """ Ensure that PAS is configured after the configuration """
    self.assertEqual(self.portal.portal_templates.TemplateTool_checkSlapOSPASConsistency(),
      [])
    self.assertEqual(self.portal.portal_templates.TemplateTool_checkSlapOSPASConsistency(),
      [])
    

  def testInteractionDropped(self):
    """ Make sure that no portal type uses interaction workflow for simulation """
    for pt in self.portal.portal_types.objectValues():
      for dropped_workflow in [
            "delivery_movement_simulation_interaction_workflow",
            "delivery_simulation_interaction_workflow",
            "open_order_simulation_interaction_workflow",
            "open_order_path_simulation_interaction_workflow",
            "container_interaction_workflow",
            "transformation_interaction_workflow",
            "trade_model_line_interaction_workflow"]:
        self.assertNotIn(dropped_workflow,
              pt.getTypeWorkflowList(),
              "Workflow %s still present on %s Portal Type (%s)" % \
                      (dropped_workflow, pt, pt.getTypeWorkflowList()))

  def test_Module_checkSlapOSModuleIdGeneratorConsistency(self):
    """ Ensure the Constraint sets appropriate id generator on all modules.
    """
    module_list = [module.getId() for module in self.portal.objectValues()
                     if getattr(module, "getIdGenerator", None) is not None and \
                                        module.getIdGenerator() == "_generatePerDayNodeNumberId"]
    expected_module_list = [
      module.getId() for module in self.portal.objectValues() if module.getId().endswith("_module")]

    expected_module_list.extend([
      'portal_activities',
      'portal_simulation',
    ])

    self.assertSameSet(module_list, expected_module_list)

  def testConfiguredBusinessTemplateList(self):
    """ Make sure Installed business Templates are
        what it is expected.  """

    expected_business_template_list = self.getExpectedBusinessTemplateInstalledAfterConfiguration()

    # If mixin contains a custom definition that introduce new business templated from
    # the project scope, them include it on expected list.
    expected_business_template_list.extend(self._custom_additional_bt5_list)

    self.assertSameSet(expected_business_template_list,
      self.portal.portal_templates.getInstalledBusinessTemplateTitleList())

  def testConfiguredExpectedBusinessTemplateDependencyList(self):
    """ Make sure TemplateTool_getSlapOSMasterBusinessTemplateList dependency resolution
        provides the expected bt5 list. """

    expected_business_template_list = self.getExpectedBusinessTemplateInstalledAfterConfiguration()

    # If mixin contains a custom definition that introduce new business templated from
    # the project scope, them include it on expected list.
    expected_business_template_list.extend(self._custom_additional_bt5_list)

    bt5_to_resolve, _, _ = self.portal.portal_templates.TemplateTool_getSlapOSMasterBusinessTemplateList()

    bt5_list = [i[1] for i in self.portal.portal_templates.resolveBusinessTemplateListDependency(
        template_title_list=bt5_to_resolve,
        with_test_dependency_list=True)]
    self.assertSameSet(expected_business_template_list, bt5_list)