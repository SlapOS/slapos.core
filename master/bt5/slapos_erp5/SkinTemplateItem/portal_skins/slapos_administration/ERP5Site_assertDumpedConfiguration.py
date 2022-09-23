portal = context.getPortalObject()
import difflib
current_confguration = portal.ERP5Site_saveDumpedConfiguration(save=0)
try:
  save_file = portal.document_module[filename]
except KeyError:
  raise ValueError("You must save the dumped configuration first with ERP5Site_saveDumpedConfiguration")

saved_configuration = save_file.getData()

return '\n'.join(difflib.unified_diff(saved_configuration.split("\n"), current_confguration.split("\n")))
