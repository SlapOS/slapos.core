if not context.getReference():
  return context.Base_redirect('view',keep_items={'portal_status_message': 'Reference is not defined'})


data_supply = context.portal_catalog.getResultValue(
  validation_state='validated',
  reference = context.getReference(),
  portal_type='Data Supply')

if data_supply:
  if batch:
    return data_supply
  return data_supply.Base_redirect('view',keep_items={'portal_status_message': 'Data Supply already created'})

data_supply = context.data_supply_module.newContent(
  portal_type = 'Data Supply',
  reference = context.getReference()
)

data_supply.newContent(
  portal_type='Data Supply Line',
  title='Data Stream',
  reference='out_stream',
  quantity=1,
  int_index=2,
  use='big_data/ingestion/stream',
  resource_uid=context.getUid()
).validate()

data_supply.newContent(
  portal_type='Data Supply Line',
  title='Ingest Data',
  reference='ingestion_operation',
  quantity=1,
  int_index=1,
  resource='data_operation_module/wendelin_ingest_data'
).validate()

data_supply.validate()
if batch:
  return data_supply
return data_supply.Base_redirect('view',keep_items={'portal_status_message': 'Data Supply is created'})
