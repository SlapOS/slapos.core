from hashlib import md5
return context.Base_renderForm(
    'SoftwareProductModule_viewParameterEditorTestResultDialog', 
    message='Show Parameters posted.',
    keep_items={'url_string': field_your_url_string,
      "software_type": software_type,
      "text_content": text_content,
      "text_content_md5": md5(text_content).hexdigest()})
