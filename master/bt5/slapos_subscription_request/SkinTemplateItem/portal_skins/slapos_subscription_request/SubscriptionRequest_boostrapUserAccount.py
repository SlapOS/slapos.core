# Send an email for the user with a URL, so he can set the password.

from Products.ERP5Type.Errors import UnsupportedWorkflowMethod

portal = context.getPortalObject()
portal_preferences = portal.portal_preferences

reference = None
password = None

person = context.getDestinationSectionValue(portal_type="Person")

if person.getDefaultEmailText() is None:
  person.setDefaultEmailText(context.getDefaultEmailText())

if person.getLanguage() in [None, ""]:
  person.setLanguage(context.getLanguage())

# Should come from subscription condition probably or preference
role_list = ['member', 'subscriber']

open_assignment_list = person.searchFolder(portal_type="Assignment",
                                              validation_state="open")

# Initialisation
assignment_duration = portal_preferences.getPreferredCredentialAssignmentDuration()
today = DateTime()
delay = today+assignment_duration

current_assignment_list = {}
for assignment in open_assignment_list:
  role = assignment.getRole()
  if role in current_assignment_list:
    current_assignment_list[role].append(assignment)
  else:
    current_assignment_list[role] = [assignment]

for role in role_list:
  if role in current_assignment_list:
    #Update assignment
    for assignment in current_assignment_list[role]:
      assignment.update()
      assignment.edit(stop_date=delay)
      assignment.open()
  else:
    #Create assignment
    assignment = person.newContent(
        portal_type='Assignment',
        title = '%s Assignment' % (role.capitalize()),
        role = role,
        start_date = today - 1,
        stop_date = delay)

    assignment.open()

login_list = [x for x in person.objectValues(portal_type=['ERP5 Login', 'Google Login', 'Facebook Login']) \
              if x.getValidationState() == 'validated']

if not login_list:
  raise ValueError('Something is wrong')

login = login_list[0]
# Let's reset password if the user is his first login.
if not open_assignment_list and person.getUserId() == login_list[0].getReference():
  login.invalidate()
  login.setReference(person.getDefaultEmailText())
  reference = person.getDefaultEmailText()
  # Update password of the user
  password = person.Person_generatePassword()
  login.setPassword(password)
  login.validate()

# Update Roles and Title
try:
  person.validate()
except UnsupportedWorkflowMethod:
  pass

person.edit(default_career_role_list=role_list)

default_career = getattr(person,'default_career',None)
#Try to validate the default career
try:
  default_career.start()
  default_career.setStartDate(DateTime())
except UnsupportedWorkflowMethod:
  pass

context.activate(activity='SQLQueue').SubscriptionRequest_sendAcceptedNotification(reference, password)

context.order()
