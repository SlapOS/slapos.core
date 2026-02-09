# Ensure user agent is stable for both GET and POST
return value == context.REQUEST.getHeader('User-Agent', None)
