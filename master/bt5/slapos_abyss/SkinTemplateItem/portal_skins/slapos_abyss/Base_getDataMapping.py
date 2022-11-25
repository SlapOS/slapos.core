mapping_for_path = getattr(context.data_mapping_module, 'mapping_for_path', None)

if not mapping_for_path:
  mapping_for_path = context.data_mapping_module.newContent(
    portal_type='Data Mapping',
    reference='mapping_for_path',
    id='mapping_for_path')
  mapping_for_path.validate()

return mapping_for_path
