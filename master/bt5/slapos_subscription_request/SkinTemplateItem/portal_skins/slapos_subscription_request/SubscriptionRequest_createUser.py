from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person is None:
  # Create a Person document in order to generate the invoice.
  person = portal.person_module.newContent(
    portal_type="Person",
    default_email_text=email,
    first_name=name)

  login = person.newContent(portal_type="ERP5 Login",
                    reference=email,
                    # Please generate a LAAARGE random password.
                    password=email)

  login.validate()
  person.validate()

  person.SubscriptionRequest_saveTransactionalUser(person)
return person
