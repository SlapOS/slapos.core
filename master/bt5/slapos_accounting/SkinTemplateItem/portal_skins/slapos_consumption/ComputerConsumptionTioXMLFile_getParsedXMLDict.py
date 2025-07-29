from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

document = context
message_list = []
try:
  tioxml_dict = document.ComputerConsumptionTioXMLFile_parseXml()
except KeyError:
  # For consistency return a validation error
  raise ValueError("Fail to parse the XML!")

if tioxml_dict is None:
  raise ValueError("Not usable TioXML data")

for prop in ['movement', 'start_date', 'stop_date']:
  if not tioxml_dict.get(prop, None):
    message_list.append("%s is missing." % prop)

if len(message_list):
  raise ValueError(" ".join(message_list))

if tioxml_dict['stop_date'] > DateTime():
  raise ValueError("You cannot invoice future consumption %s" % tioxml_dict['stop_date'])

for movement in tioxml_dict["movement"]:
  reference = movement.get('reference', None)
  if not reference:
    message_list.append("One of Movement has no reference (%s)." % movement['title'])

  resource = movement.get('resource', None)
  if not resource:
    message_list.append("Movement without resource (%s)" % movement['title'])

if message_list:
  raise ValueError(" ".join(message_list))

return tioxml_dict
