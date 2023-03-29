from zExceptions import Unauthorized
import random, string

if REQUEST is not None:
  raise Unauthorized


portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person is not None:
  # Person already existed
  return person, False

# Already has login with this.
person = context.SubscriptionRequest_searchExistingUserByEmail(email)
if person is not None:
  return person, False

# Create a Person document in order to generate the invoice.
person = portal.person_module.newContent(
  portal_type="Person",
  first_name=name)

for role in ['member', 'subscriber']:
  person.newContent(
    portal_type='Assignment',
    title = '%s Assignment' % (role.capitalize()),
    role = role).open(comment="Created by Subscription Request")

password = list("".join([context.Person_generatePassword(15, 5, 4) for _ in range(random.randint(2, 4))]))
random.shuffle(password)

login = person.newContent(
  portal_type="ERP5 Login",
  reference="%s-FIRST-SUBSCRIBER-LOGIN" % person.getUserId(),
  password="".join(password))

login.validate()


# The rest of the information will be used later.
person.SubscriptionRequest_saveTransactionalUser(person)

# New user is created
return person, True
