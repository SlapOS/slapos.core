import numpy as np
from Products.ZSQLCatalog.SQLCatalog import AndQuery, Query

# for reference image, archive previous version, then change state

publication_section_list = context.getPublicationSectionList()
if 'file_system_image/reference_image' in publication_section_list:
  distribution = [x for x in publication_section_list if 'distribution' in x][0]
  query = AndQuery(
    Query(portal_type = ["Data Array"]),
    Query(simulation_state = ("processed")),
    AndQuery(Query(publication_section_relative_url = 'publication_section/file_system_image/reference_image'),
             Query(publication_section_relative_url = 'publication_section/%s' % distribution)))
  for old_version in context.portal_catalog(query=query):
    old_version.archiveFile()
  context.processFile()
  return

# Get current distribution
for publication_section in context.getPublicationSectionList():
  if 'distribution' in publication_section:
    current_node_distribution = publication_section

reference_distribution = None

for predecessor in context.getPredecessorValueList(
  portal_type='Data Array'
):
  publication_section_list = predecessor.getPublicationSectionList()
  if 'file_system_image/reference_image' in publication_section_list:
    for publication_section in publication_section_list:
      if 'distribution' in publication_section:
        distribution_property = context.portal_categories.restrictedTraverse('publication_section/%s' % publication_section)
        #file_system_image/distribution/debian/debian10
        parent_distribution = distribution_property.getParentValue()
        distribution_list = [x for x in parent_distribution.objectValues(sort_on='int_index')]
        index = distribution_list.index(distribution_property) + 1
        if index >= len(distribution_list):
          context.setPublicationSectionList(context.getPublicationSectionList() + ['publication_section/file_system_image/diff_end'])
          causality = context.getCausalityValue(portal_type='Data Product')
          if causality and context.portal_workflow.isTransitionPossible(causality, 'invalidate'):
            causality.invalidate(comment='Server has file modified: %s' % context.getRelativeUrl())
          context.processFile()
          return
        reference_distribution = distribution_list[index].getRelativeUrl()

# It's a new one
if not reference_distribution:
  reference_distribution = 'publication_section/%s' % current_node_distribution

query = AndQuery(
          Query(portal_type = ["Data Array"]),
          Query(simulation_state = ("converted", "processed")),
          AndQuery(Query(publication_section_relative_url = 'publication_section/file_system_image/reference_image'),
                   Query(publication_section_relative_url = reference_distribution)))

reference_image_list = context.portal_catalog(query=query)

reference_image = None
if reference_image_list:
  # always take converted state one, which is the latest version
  for last_one in reference_image_list:
    if last_one.getSimulationState() == "converted":
      break
  reference_image = last_one


def getDiff(a1, a2):
  return np.setdiff1d(a1[:], a2[:])

if reference_image:
  diff_array = getDiff(context.getArray(), reference_image.getArray())
  if len(diff_array) != 0:
    new_data_array = context.data_array_module.newContent(portal_type='Data Array')
    new_data_array.setArray(diff_array)
    new_data_array.edit(
      predecessor_value_list=[context, reference_image],
      publication_section="file_system_image/node_image",
      causality = context.getCausality()
    )
    new_data_array.convertFile()
  else:
    causality = context.getCausalityValue(portal_type='Data Product')
    if causality and context.portal_workflow.isTransitionPossible(causality, 'validate'):
      causality.validate(comment='Server is ok')
    context.setPublicationSectionList(context.getPublicationSectionList() + ['publication_section/file_system_image/diff_end'])

else:
  causality = context.getCausalityValue(portal_type='Data Product')
  if causality and context.portal_workflow.isTransitionPossible(causality, 'invalidate'):
    causality.invalidate(comment='Server has file modified: %s' % context.getRelativeUrl())
  context.setPublicationSectionList(context.getPublicationSectionList() + ['publication_section/file_system_image/diff_end'])

context.processFile()