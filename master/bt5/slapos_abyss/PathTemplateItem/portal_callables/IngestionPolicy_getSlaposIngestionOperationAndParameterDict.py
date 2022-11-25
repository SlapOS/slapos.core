from DateTime import DateTime

now = DateTime()
today_string = now.strftime('%Y%m%d')
portal = context.getPortalObject()
portal_catalog = portal.portal_catalog

reference = movement_dict.get('reference', reference)
data_ingestion_id =  "%s-%s" %(today_string, reference)

data_ingestion_query_kw = dict(
  portal_type = 'Data Ingestion',
  simulation_state = ['started', 'stopped'],
  reference = reference)

# first search for applicable data ingestion
data_ingestion = portal_catalog.getResultValue(**data_ingestion_query_kw)

def init_input_line(input_line, operation_line):
  input_line.setAggregateSet(
    input_line.getAggregateList() + operation_line.getAggregateList())

  data_stream = portal.portal_catalog.getResultValue(
    portal_type='Data Stream',
    validation_state="validated",
    item_device_relative_url=operation_line.getAggregateDevice(),
    item_project_relative_url=input_line.getDestinationProject(),
    item_resource_uid=input_line.getResourceUid())

  if data_stream is None:
    compute_node = portal.portal_catalog.getResultValue(
      portal_type = "Compute Node",
      reference = reference
    )
    data_stream = portal.data_stream_module.newContent(
      portal_type = 'Data Stream',
      publication_section_list = compute_node.getPublicationSectionList(),
      source=compute_node.getRelativeUrl(),
      reference = reference)
    data_stream.validate()

  input_line.setAggregateValueList(
                            input_line.getAggregateValueList() + [data_stream])
  input_line.setQuantity(1)


if data_ingestion is None:
  document = portal.data_ingestion_module.get(data_ingestion_id)
  if (document is not None) and document.getSimulationState() in ('started', 'stopped'):
    data_ingestion = document

if data_ingestion is None:
  specialise_query_kw = dict(portal_type = 'Data Supply',
    reference = reference,
    validation_state = 'validated')
  specialise_list = [x.getRelativeUrl() for x in portal_catalog(**specialise_query_kw)]
  # create a new data ingestion
  data_ingestion = portal.ERP5Site_createDataIngestion(specialise_list,
                                                       reference,
                                                       data_ingestion_id)
  for line in data_ingestion.objectValues(portal_type='Data Ingestion Line'):
    # Mark so initialize later
    if line.getResourceValue().getPortalType() == "Compute Node":
      line.setQuantity(0)
      break

for line in data_ingestion.objectValues(portal_type="Data Ingestion Line"):
  if line.getResourceReference() == reference:
    input_line = line
  elif line.getResourceValue().getPortalType() == "Data Operation":
    operation_line = line

if input_line.getQuantity() == 0:
  init_input_line(input_line, operation_line)

data_operation = operation_line.getResourceValue()
parameter_dict = {
   input_line.getReference(): \
     {v.getPortalType(): v for v in input_line.getAggregateValueList()}}


return data_operation, parameter_dict
