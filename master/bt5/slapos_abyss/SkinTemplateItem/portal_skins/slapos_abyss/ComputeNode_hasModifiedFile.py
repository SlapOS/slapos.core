from Products.ZSQLCatalog.SQLCatalog import AndQuery, Query

query = AndQuery(
    Query(portal_type = ["Data Array"]),
    Query(causality_uid=context.getUid()),
    AndQuery(Query(publication_section_relative_url = 'publication_section/file_system_image/diff_end'),
             Query(publication_section_relative_url = 'publication_section/file_system_image/process_state/processed')))


data_array = context.portal_catalog.getResultValue(
  query=query,
  sort_on=[('creation_date', 'descending')])

if data_array:
  if "file_system_image/diff_end/different" in data_array.getPublicationSectionList():
    return data_array
return None
