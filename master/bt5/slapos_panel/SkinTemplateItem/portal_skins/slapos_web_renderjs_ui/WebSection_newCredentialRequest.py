"""Call by dialog to create a new credential request and redirect to the context
Paramameter list :
reference -- User login is mandatory (String)
default_email_text -- Email is mandatory (String)"""
# create the credential request
import binascii
from Products.ERP5Type.Utils import bytes2str, str2bytes

portal = context.getPortalObject()
module = portal.getDefaultModule(portal_type='Credential Request')
portal_preferences = portal.portal_preferences
category_list = portal_preferences.getPreferredSubscriptionAssignmentCategoryList()

if not context.CredentialRequest_checkLoginAvailability(reference):
  message_str = "Selected login is already in use, please choose different one."
  return context.REQUEST.RESPONSE.redirect(context.absolute_url() + "/join_form?portal_status_message=" + context.Base_translateString(message_str))

credential_request = module.newContent(
                portal_type="Credential Request",
                first_name=first_name,
                last_name=last_name,
                reference=reference,
                password=password,
                default_credential_question_question=default_credential_question_question,
                default_credential_question_question_free_text=default_credential_question_question_free_text,
                default_credential_question_answer=default_credential_question_answer,
                default_email_text=default_email_text,
                default_telephone_text=default_telephone_text,
                default_mobile_telephone_text=default_mobile_telephone_text,
                default_fax_text=default_fax_text,
                default_address_street_address=default_address_street_address,
                default_address_city=default_address_city,
                default_address_zip_code=default_address_zip_code,
                default_address_region=default_address_region,
                role_list=role_list,
                function=function,
                site=site,
                activity_list=activity_list,
                corporate_name=corporate_name,
                date_of_birth=date_of_birth)

credential_request.setCategoryList(category_list)
# Same tag is used as in ERP5 Login._setReference, in order to protect against
# concurrency between Credential Request and Person object too
tag = 'set_login_%s' % bytes2str(binascii.hexlify(str2bytes(reference)))
credential_request.reindexObject(activate_kw={'tag': tag})

if portal_preferences.getPreferredCredentialAlarmAutomaticCall():
  portal_type = context.Base_translateString("Credential Request")
  credential_request.submit("Automatic submit")
  message_str = context.Base_translateString("${portal_type} Created.", mapping=({'portal_type': portal_type}))
else:
  if portal_preferences.isPreferredEmailVerificationCheck():
    # after_path_and_method_id argument is used below to not activate when
    # Crededial request object is not indexed yet. This is needed because when
    # the method searchAndActivate from catalog is called, if the object is not
    # indexed, the e-mail is not sent.
    method_id_list = ('immediateReindexObject', 'recursiveImmediateReindexObject')
    path_and_method_id = (credential_request.getPath(), method_id_list)
    activity_kw = dict(activity='SQLQueue',
                       after_path_and_method_id=path_and_method_id)
    credential_request.activate(**activity_kw).CredentialRequest_sendSubmittedNotification(
      context_url=context.absolute_url(),
      notification_reference='credential_request-subscription')
    message_str = "Thank you for your registration. You will receive an email to activate your account."
  else:
    # no email verification is needed
    portal_type = context.Base_translateString("Credential Request")
    credential_request.submit("Automatic submit")
    message_str = context.Base_translateString("${portal_type} Created.", mapping=({'portal_type': portal_type}))

if batch_mode:
  return credential_request

return context.REQUEST.RESPONSE.redirect(context.absolute_url() + "/login_form?portal_status_message=" + context.Base_translateString(message_str))
