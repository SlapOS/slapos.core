last_message = context.getPortalObject().MailHost.getMessageList()[-1]

assert last_message[1] == ['Demo User Functional <demo@nexedi.com>']
assert "WebSite_viewResetPassword" in last_message[2]

# Find the url in a dummiest way as possible
message = last_message[2].replace("\n", " ")
for _word in message.split(" "):
  if "WebSite_viewResetPassword?reset_key" in _word:
    container.REQUEST.REPONSE.setHeader('Content-Type', 'text/html')
    return "<a href='%s' name='reset_password'>Reset Password link sent by mail </a>" % _word.strip()
