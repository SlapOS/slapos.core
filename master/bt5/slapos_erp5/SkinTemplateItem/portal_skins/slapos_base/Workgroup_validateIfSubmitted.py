workgroup = context

if workgroup.getValidationState() != 'submitted':
  return

person = context.getDestinationValue()
if person is None:
  raise ValueError('Not possible to find the user to create the initial assignment')
if activate_kw is None:
  activate_kw = {}

if 'tag' not in activate_kw:
  activate_kw['tag'] = "%s_validate" % context.getRelativeUrl()

# We create the assignment directly to automatically give
# access to the Owner, later the Missing Assignment Request
# will be created.
assignment = person.newContent(
  portal_type='Assignment',
  title='%s: %s' % (workgroup.getTitle(), person.getTitle()),
  destination_value=workgroup,
  activate_kw=activate_kw
)
assignment.open(comment='Open automatically from the Workgroup validation')

workgroup.activate(after_tag=activate_kw['tag']).validate(
  comment='Validated after create the initial assignment: %s' % assignment.getTitle())
