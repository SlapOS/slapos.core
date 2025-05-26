portal = context.getPortalObject()
from Products.ERP5Type.Utils import str2bytes
msg = ""

def render(title, body):
  return """########################################################################
# %s
########################################################################
%s
########################################################################

""" % (title, body)

msg += render("Alarm Configuration Diff",
  portal.ERP5Site_dumpAlarmToolConfiguration())

msg += render("Builder Configuration Diff",
  portal.ERP5Site_dumpBuilderList())

msg += render("Business Template Configuration Diff",
  portal.ERP5Site_dumpInstalledBusinessTemplateList())

msg += render("Order Builder Configuration Diff",
  portal.ERP5Site_dumpOrderBuilderList())

msg += render("Property Sheet Configuration Diff",
  portal.ERP5Site_dumpPropertySheetList())

msg += render("Skins Configuration Diff",
  portal.ERP5Site_dumpPortalSkinsContent())

msg += render("Web Content Configuration Diff",
  portal.ERP5Site_dumpWebPageModuleContent())

msg += render("Portal Type Actions Configuration Diff",
  portal.ERP5Site_dumpPortalTypeActionList())

msg += render("Portal Type Configuration Diff",
    portal.ERP5Site_dumpPortalTypeList())

msg += render("Role Configuration Diff",
  portal.ERP5Site_dumpPortalTypeRoleList())

msg += render("Rule Configuration Diff",
  portal.ERP5Site_dumpRuleTesterList())

msg += render("Skin Property Configuration Diff",
  portal.ERP5Site_dumpSkinProperty())

msg += render("Workflow Configuration Diff",
  portal.ERP5Site_dumpWorkflowChain())

if save:
  module = portal.document_module
  try:
    save_file = portal.document_module['erp5_dumped_configuration']
  except KeyError:
    backup = 0
    save_file = module.document_module.newContent(
      id='erp5_dumped_configuration',
      portal_type='File')

  if backup:
    # We should only backup on really special cases
    backup_file = module.document_module.newContent(
      reference='F-backuped-configuration',
      portal_type='File')
    backup_file.setData(save_file.getData())

  save_file.setData(str2bytes(msg))

return msg
