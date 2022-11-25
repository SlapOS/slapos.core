data_analysis_line = context.getResourceRelatedValue(portal_type='Data Analysis Line')

return data_analysis_line.Base_jumpToRelatedObject(portal_type='Data Stream', base_category='aggregate', related=0)
