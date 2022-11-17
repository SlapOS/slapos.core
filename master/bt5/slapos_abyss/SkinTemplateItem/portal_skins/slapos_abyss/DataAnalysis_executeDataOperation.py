portal = context.getPortalObject()
operation = None
use_list = []
parameter_dict = {}

transient_output_item = None
context.checkConsistency(fixit=True)
initial_product = context.getSpecialiseValue(portal_type="Data Transformation").getResourceValue()

for analysis_line in context.objectValues(portal_type="Data Analysis Line"):
  if analysis_line.getQuantity() < 0:
    indicator = analysis_line.getAggregateProgressIndicatorValue()
    stream = analysis_line.getAggregateDataStreamValue()
    if indicator and stream and indicator.getIntOffsetIndex() >= stream.getSize():
      return

for analysis_line in sorted(context.objectValues(portal_type="Data Analysis Line"),
                           key=lambda x: x.getIntIndex()):
  resource = analysis_line.getResourceValue()
  if resource == initial_product:
    use_list = analysis_line.getUseList()
  if resource is not None:
    resource_portal_type = resource.getPortalType()
  else:
    resource_portal_type = ''
  if resource_portal_type == 'Data Operation':
    operation_analysis_line = analysis_line
    operation = analysis_line.getResourceValue()
  else:
    parameter = {}
    for portal_type in ["Data Array View", "Progress Indicator"] + \
                        list(portal.getPortalDataSinkTypeList()) + \
                        list(portal.getPortalDataDescriptorTypeList()):
      value = analysis_line.getAggregateValue(portal_type=portal_type)
      if value is not None:
        parameter[portal_type] = value
    # Input line, get correct data stream and mapping
    if analysis_line.getQuantity() < 0:
      if "Data Stream" not in parameter:
        data_ingestion = analysis_line.getCausalityValue(portal_type='Data Ingestion')
        data_stream_line = [x for x in data_ingestion.objectValues(portal_type='Data Ingestion Line') if x.getReference() =='out_stream'][0]
        data_stream = data_stream_line.getAggregateDataStreamValue()
        analysis_line.setAggregateValueList(analysis_line.getAggregateValueList() + [data_stream])
        parameter['Data Stream'] = data_stream

      parameter['Data Mapping'] = analysis_line.Base_getDataMapping()

    # Get Correct Data array
    data_array_list = analysis_line.getAggregateValueList(portal_type='Data Array')
    if data_array_list:
      all_data_array_is_processed = True
      for data_array in data_array_list:
        if data_array.getSimulationState() not in ('processed', 'archived'):
          all_data_array_is_processed = False
          break

      if all_data_array_is_processed:
        module = portal.getDefaultModule('Data Array')
        data_array = module.newContent(portal_type = 'Data Array',
                                       title = initial_product.getTitle(),
                                       reference = data_array.getReference()
                                      )
        analysis_line.setAggregateValueList(analysis_line.getAggregateValueList() + [data_array])

      parameter['Data Array'] = data_array

    if analysis_line.getQuantity() < 0 and "big_data/analysis/transient" in analysis_line.getUseList():
      # at the moment we only support transient data arrays
      parameter['Data Array'] = transient_input_item
    if analysis_line.getQuantity() > 0 and "big_data/analysis/transient" in analysis_line.getUseList():
      # at the moment we only support transient data arrays
      transient_output_item = portal.data_array_module.newContent(portal_type='Data Array',
                                                                  temp_object=True)
      parameter['Data Array'] = transient_output_item
    for base_category in analysis_line.getVariationRangeBaseCategoryList():
      parameter[base_category] = analysis_line.getVariationCategoryItemList(
                                   base_category_list=(base_category,))[0][0]
    reference = analysis_line.getReference()

    parameter["Start Date"] = analysis_line.getStartDate()
    parameter["Stop Date"] = analysis_line.getStopDate()
    parameter["causality_reference"] = analysis_line.getCausalityReference()
    parameter["causality_relative_url"] = analysis_line.getCausality()
    parameter["reference"] = analysis_line.getReference()
    # several lines with same reference wil turn the parameter into a list
    if reference in parameter_dict:
      if not isinstance(parameter_dict[reference], list):
        parameter_dict[reference] = [parameter_dict[reference]]
      parameter_dict[reference].append(parameter)
    else:
      parameter_dict[reference] = parameter

if consuming_analysis_list is None:
  consuming_analysis_list = []
if transient_output_item is not None and not consuming_analysis_list:
  return

script_id = operation.getScriptId()
out = getattr(operation_analysis_line, script_id)(**parameter_dict)

for consuming_analysis in consuming_analysis_list:
  portal.restrictedTraverse(consuming_analysis).DataAnalysis_executeDataOperation(transient_input_item = transient_output_item)

if out == 1:
  context.activate(serialization_tag=str(context.getUid())).DataAnalysis_executeDataOperation(consuming_analysis_list)
else:
  # only stop batch ingestions
  if "big_data/ingestion/batch" in use_list:
    context.stop()
  # stop refresh
  if context.getRefreshState() == "refresh_started":
    context.stopRefresh()

return out
