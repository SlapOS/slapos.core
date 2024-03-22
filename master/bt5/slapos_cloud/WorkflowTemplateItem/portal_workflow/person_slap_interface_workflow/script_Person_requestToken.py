person = state_change['object']
portal = person.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  request_url = kwargs['request_url']
except KeyError:
  raise TypeError("Person_requestToken takes exactly 1 argument")

request_method = "POST"
access_token = portal.access_token_module.newContent(
  portal_type="One Time Restricted Access Token",
  agent_value=person,
  url_string=request_url,
  url_method=request_method
)
access_token_id = access_token.getId()
access_token.validate()

context.REQUEST.set("token", access_token_id)
