data_array = context.portal_catalog(
  portal_type='Data Array',
  simulation_state='processed',
  causality_uid = context.getUid(),
  publication_section_relative_url='publication_section/file_system_image/diff_end',
  sort_on=[('creation_date', 'descending')],
  limit=1)

if data_array:
  if "file_system_image/diff_end/different" in data_array[0].getPublicationSectionList():
    return data_array[0]
return None
