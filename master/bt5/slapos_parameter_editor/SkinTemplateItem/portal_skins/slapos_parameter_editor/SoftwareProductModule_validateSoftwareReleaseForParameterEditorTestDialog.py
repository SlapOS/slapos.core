return context.Base_renderForm(
    'SoftwareProductModule_viewParameterEditorTestDialog', 
    message='View Parameter Editor',
    keep_items={'url_string': url_string,
      "text_content": text_content or '<instance/>',
      "softwaretype": softwaretype,
      "read_only": read_only})
