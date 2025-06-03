portal = context.getPortalObject()
import difflib
from Products.ERP5Type.Utils import bytes2str
current_confguration = portal.ERP5Site_saveDumpedConfiguration(save=0).split("\n")
try:
  save_file = portal.document_module[filename]
except KeyError:
  raise ValueError("You must save the dumped configuration first with ERP5Site_saveDumpedConfiguration")

saved_configuration = bytes2str(save_file.getData()).split("\n")

return '\n'.join(difflib.unified_diff(saved_configuration, current_confguration))
