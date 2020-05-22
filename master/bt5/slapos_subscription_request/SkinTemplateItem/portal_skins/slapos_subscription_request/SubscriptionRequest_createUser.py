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

password = [random.choice(string.upper(string.ascii_letters)),
            random.choice(string.lower(string.ascii_letters)),
            random.choice(string.digits),
            random.choice("$!*#%$.;:,")]

chars = string.ascii_letters + string.digits + '!@#$%^&*()'
password.extend([random.choice(chars) for _ in range(26)])

random.shuffle(password)

login = person.newContent(
  portal_type="ERP5 Login",
  reference=person.getUserId(),
  password=''.join(password))

login.validate()


# The rest of the information will be used later.
person.SubscriptionRequest_saveTransactionalUser(person)

# New user is created
return person, True
