import numpy as np
from Products.ZSQLCatalog.SQLCatalog import AndQuery, Query

# for database image, archive previous version, then change state

publication_section_list = context.getPublicationSectionList()
if 'file_system_image/database_image' in publication_section_list:
  distribution = [x for x in publication_section_list if 'distribution' in x][0]
  query = AndQuery(
    Query(portal_type = ["Data Array"]),
    Query(simulation_state = ("processed")),
    AndQuery(Query(publication_section_relative_url = 'publication_section/file_system_image/database_image'),
             Query(publication_section_relative_url = 'publication_section/%s' % distribution)))
  for old_version in context.portal_catalog(query=query):
    old_version.archiveFile()
  context.processFile()
  return

# Get current distribution
for publication_section in context.getPublicationSectionList():
  if 'distribution' in publication_section:
    current_node_distribution = publication_section

database_distribution = None

for predecessor in context.getPredecessorValueList(
  portal_type='Data Array'
):
  publication_section_list = predecessor.getPublicationSectionList()
  if 'file_system_image/database_image' in publication_section_list:
    for publication_section in publication_section_list:
      if 'distribution' in publication_section:
        distribution_property = context.portal_categories.restrictedTraverse('publication_section/%s' % publication_section)
        #file_system_image/distribution/debian/debian10
        parent_distribution = distribution_property.getParentValue()
        distribution_list = [x for x in parent_distribution.objectValues(sort_on='int_index')]
        index = distribution_list.index(distribution_property) + 1
        if index >= len(distribution_list):
          context.setPublicationSectionList(context.getPublicationSectionList() + ['publication_section/file_system_image/diff_end/different'])
          context.processFile()
          return
        database_distribution = distribution_list[index].getRelativeUrl()

# It's a new one
if not database_distribution:
  database_distribution = 'publication_section/%s' % current_node_distribution

query = AndQuery(
          Query(portal_type = ["Data Array"]),
          Query(simulation_state = ("converted", "processed")),
          AndQuery(Query(publication_section_relative_url = 'publication_section/file_system_image/database_image'),
                   Query(publication_section_relative_url = database_distribution)))

database_image_list = context.portal_catalog(query=query, sort_on=[('creation_date', 'descending')], limit=1)

def getDiff(a1, a2):
  return np.setdiff1d(a1[:], a2[:])


if database_image_list:
  database_image = database_image_list[0]
  diff_array = getDiff(context.getArray(), database_image.getArray())
  if len(diff_array) != 0:
    new_data_array = context.data_array_module.newContent(portal_type='Data Array')
    new_data_array.setArray(diff_array)
    new_data_array.edit(
      title='diff of %s and %s' %(context.getTitle(), database_image.getTitle()),
      predecessor_value_list=[context, database_image],
      publication_section="file_system_image/node_image",
      causality = context.getCausality()
    )
    new_data_array.convertFile()
    analysis_line = context.getAggregateRelatedValue(portal_type='Data Analysis Line')
    if analysis_line:
      analysis_line.setAggregateValueList(analysis_line.getAggregateValueList() + [new_data_array])
  else:
    context.setPublicationSectionList(context.getPublicationSectionList() + ['publication_section/file_system_image/diff_end/identical'])

else:
  context.setPublicationSectionList(context.getPublicationSectionList() + ['publication_section/file_system_image/diff_end/different'])

context.processFile()
