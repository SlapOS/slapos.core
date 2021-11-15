if not context.getReference():
  return context.Base_redirect('view',keep_items={'portal_status_message': 'Reference is not defined'})


data_transformation = context.portal_catalog(
  validation_state='validated',
  resource_relative_url = context.getRelativeUrl(),
  portal_type='Data Transformation')

if data_transformation:
  if batch:
    return data_transformation
  return data_transformation.Base_redirect('view',keep_items={'portal_status_message': 'Data Transformation already created'})

data_transformation = context.data_transformation_module.newContent(
  portal_type = 'Data Transformation',
  reference = context.getReference(),
  title='Data transformation for %s' % context.getTitle(),
  resource_uid=context.getUid()
)

data_transformation.newContent(
  portal_type='Data Transformation Resource Line',
  title='In Stream',
  reference='in_stream',
  quantity=-1,
  int_index=1,
  aggregated_portal_type_list = ['Data Stream', 'Progress Indicator'],
  trade_phase='data/convert',
  resource_uid=context.getUid()
)

data_transformation.newContent(
  portal_type='Data Transformation Resource Line',
  title='Out Array',
  reference='out_array',
  quantity=1,
  int_index=2,
  aggregated_portal_type_list = ['Data Array'],
  trade_phase='data/convert',
  use='big_data/ingestion/stream',
  resource='data_product_module/convert_data_stream_to_data_array'
)

data_transformation.newContent(
  portal_type='Data Transformation Operation Line',
  title='Convert Raw Data to Array',
  reference='data_operation',
  quantity=1,
  int_index=3,
  resource='data_operation_module/convert_raw_data_to_array_data_operation'
)

data_transformation.validate()
if batch:
  return data_transformation
return data_transformation.Base_redirect('view',keep_items={'portal_status_message': 'Data Transformation is created'})
