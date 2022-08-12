# It is important to acquire the project from the context
# and not from the portal, to ensure all hateoas URLs
# are correctly generated from the context (and so, the acquired web section)
project = context.restrictedTraverse(project_relative_url)

return project.Base_renderForm(
  'Project_viewRequestPayableSoftwareProductDialog'
)
