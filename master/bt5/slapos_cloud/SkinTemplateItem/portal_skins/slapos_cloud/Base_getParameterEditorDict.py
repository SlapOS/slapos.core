import base64

text_content = context.getTextContent()
if context.getTextContent() is None:
  text_content = '<?xml version="1.0" encoding="utf-8" ?><instance></instance>'

parameter_dict = {
    'parameter' : {
      'json_url': ".".join([context.getUrlString(), "json"]),
      'softwaretype': context.getSourceReference(),
      'shared': context.getRootSlave(),
      'parameter_hash': base64.b64encode(text_content)
    }
  }
import json
return json.dumps(parameter_dict)
