from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

assignment_category_set = set(assignment_category_list)
person = context.getParentValue()

# check if user has an assignment matching the default preference
has_default_assignment = False
has_open_assignment = False
for assignment in person.contentValues(
  portal_type='Assignment'
):
  if assignment.getValidationState() != 'open':
    continue
  has_open_assignment = True
  has_default_assignment = has_default_assignment or (assignment_category_set <= set(assignment.getCategoryList()))

if has_open_assignment and (not has_default_assignment):
  new_assignment = person.newContent(
    portal_type="Assignment",
    title="Preferred Subscription Assignment"
  )
  new_assignment.setCategoryList(assignment_category_list)
  new_assignment.open(comment="Created during the system preference subscription definition")
  new_assignment.reindexObject(activate_kw=activate_kw)
