from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery

current_publication_section_list = context.getPublicationSectionList()
portal = context.getPortalObject()

if 'file_system_image/first_access' not in current_publication_section_list:
  current_publication_section_list.append('file_system_image/first_access')
  context.setPublicationSectionList(current_publication_section_list)

if portal.portal_workflow.isTransitionPossible(context, 'validate'):
  context.validate(comment='declare as default data')

for previous_array in portal.portal_catalog(
  portal_type='Data Array',
  query=NegatedQuery(SimpleQuery(uid=context.getUid())),
  publication_section_relative_url ='publication_section/file_system_image/first_access',
  causality_uid = context.getCausalityUid(),
  validation_state='validated'
):
  previous_array.invalidate(comment="%s is declared as default data" % context.getRelativeUrl())

if batch:
  return
return context.Base_redirect('view',
  keep_items={'portal_status_message':
    context.Base_translateString("Declared as default data")})
