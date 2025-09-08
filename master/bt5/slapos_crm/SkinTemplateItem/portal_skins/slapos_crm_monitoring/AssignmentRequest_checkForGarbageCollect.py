assignment_request = context

if activate_kw is None:
  activate_kw = {}

project = assignment_request.getDestinationProjectValue(portal_type='Project')
if (project is None) or (project.getValidationState() == 'validated'):
  return

if assignment_request.getSimulationState() == 'validated':
  assignment_request.suspend(comment='Suspending as the project %s is not started anymore' % project.getRelativeUrl())
  assignment_request.reindexObject(activate_kw=activate_kw)
