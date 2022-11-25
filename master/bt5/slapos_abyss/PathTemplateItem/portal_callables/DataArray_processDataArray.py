import numpy as np
from Products.ZSQLCatalog.SQLCatalog import AndQuery, Query

# for database image, archive previous version, then change state

current_publication_section_list = context.getPublicationSectionList()

if "file_system_image/process_state/converted" in current_publication_section_list:
  current_publication_section_list.remove("file_system_image/process_state/converted")
  current_publication_section_list.append("file_system_image/process_state/processed")

if 'file_system_image/database_image' in current_publication_section_list:
  distribution = [x for x in current_publication_section_list if 'distribution' in x][0]
  query = AndQuery(
    Query(portal_type = ["Data Array"]),
    Query(validation_state = "validated"),
    AndQuery(Query(publication_section_relative_url = 'publication_section/file_system_image/process_state/processed'),
             Query(publication_section_relative_url = 'publication_section/file_system_image/database_image'),
             Query(publication_section_relative_url = 'publication_section/%s' % distribution)))
  for old_version in context.portal_catalog(query=query):
    old_version_publication_section_list =  old_version.getPublicationSectionList()
    old_version_publication_section_list.remove("file_system_image/process_state/processed")
    old_version_publication_section_list.append("file_system_image/process_state/archived")
    old_version.setPublicationSectionList(old_version_publication_section_list)
  context.setPublicationSectionList(current_publication_section_list)
  return

parent_array_list = context.getPredecessorValueList(portal_type='Data Array')

if parent_array_list:
  next_database_distribution = None
  parent_database_image = [x for x in parent_array_list if 'file_system_image/database_image' in x.getPublicationSectionList()]
  if parent_database_image:
    parent_database_image = parent_database_image[0]
    for publication_section in parent_database_image.getPublicationSectionList():
      if 'distribution' in publication_section:
        distribution_property = context.portal_categories.restrictedTraverse('publication_section/%s' % publication_section)
        #file_system_image/distribution/debian/debian10
        parent_distribution = distribution_property.getParentValue()
        distribution_list = [x for x in parent_distribution.objectValues(sort_on='int_index')]
        index = distribution_list.index(distribution_property) + 1
        # end, no more database found
        if index >= len(distribution_list):
          context.setPublicationSectionList(current_publication_section_list + [
            'file_system_image/diff_end/different'])
          return
        next_database_distribution = distribution_list[index].getRelativeUrl()
        break
  else:
    # parent are not database, so current array is result of self comparison
    first_access_image = [x for x in parent_array_list if 'file_system_image/first_access' in x.getPublicationSectionList()][0]
    for publication_section in first_access_image.getPublicationSectionList():
      if 'distribution' in publication_section:
        next_database_distribution = 'publication_section/%s' % publication_section
        break

  assert next_database_distribution is not None, "can't find next database distribution to compare"
  query = AndQuery(
    Query(portal_type = ["Data Array"]),
    Query(validation_state = "validated"),
    AndQuery(Query(publication_section_relative_url = 'publication_section/file_system_image/database_image'),
             Query(publication_section_relative_url = 'publication_section/file_system_image/process_state/processed'),
             Query(publication_section_relative_url = next_database_distribution)))
  next_database_image = context.portal_catalog.getResultValue(query=query, sort_on=[('creation_date', 'descending')])

else:
  # it's a first processing
  # it's a first access, just change state
  if 'file_system_image/first_access' in current_publication_section_list:
    context.setPublicationSectionList(current_publication_section_list)
    return
  # not a first access, so get the first access data then compare
  next_database_image = context.portal_catalog.getResultValue(
    portal_type='Data Array',
    validation_state='validated',
    publication_section_relative_url ='publication_section/file_system_image/first_access',
    causality_uid = context.getCausalityUid())



def getDiff(a1, a2):
  return np.setdiff1d(a1[:], a2[:])


if next_database_image:
  diff_array = getDiff(context.getArray(), next_database_image.getArray())
  if len(diff_array) != 0:
    new_data_array = context.data_array_module.newContent(portal_type='Data Array')
    new_data_array.setArray(diff_array)
    new_data_array.edit(
      title='diff of %s and %s' %(context.getTitle(), next_database_image.getTitle()),
      predecessor_value_list=[context, next_database_image],
      publication_section=["file_system_image/node_image", "file_system_image/process_state/converted"],
      causality = context.getCausality()
    )
    new_data_array.validate()
    analysis_line = context.getAggregateRelatedValue(portal_type='Data Analysis Line')
    if analysis_line:
      analysis_line.setAggregateValueList(analysis_line.getAggregateValueList() + [new_data_array])
    context.setPublicationSectionList(current_publication_section_list)
  else:
    context.setPublicationSectionList(current_publication_section_list + ['file_system_image/diff_end/identical'])

else:
  context.setPublicationSectionList(current_publication_section_list + ['file_system_image/diff_end/different'])
