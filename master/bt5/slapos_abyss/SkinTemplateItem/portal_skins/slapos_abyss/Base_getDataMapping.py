data_mapping_list = context.portal_catalog(portal_type='Data Mapping', reference='mapping_for_path', validation_state='validated')
if len(data_mapping_list) > 1:
  raise ValueError('multiple mapping_for_path Data Mapping')
if data_mapping_list:
  data_mapping = data_mapping_list[0]
else:
  data_mapping = context.data_mapping_module.newContent(portal_type='Data Mapping', reference='mapping_for_path')
  data_mapping.validate()
return data_mapping
