from zExceptions import Unauthorized
if REQUEST is None:
  raise Unauthorized

if REQUEST.other['method'] != "GET":
  raise ValueError("Method is not GET but a " + REQUEST.other['method'])

if default_email_text is None:
  raise ValueError("Please Provide some email!")

if name is None:
  raise ValueError("Please Provide some name!")

if subscription_reference is None:
  raise ValueError("Please Provide some subscription_reference!")

user_input_dict = {
  "name": name,
  "amount" : amount}

return context.SubscriptionRequestModule_requestSubscriptionProxy(
    default_email_text, subscription_reference,
    confirmation_required=bool(confirmation_required),
    token=token, user_input_dict=user_input_dict,
    target_language=target_language, batch_mode=0)
