if REQUEST is None:
  REQUEST = context.REQUEST
if response is None:
  response = REQUEST.RESPONSE

web_page = context

if REQUEST.getHeader('If-Modified-Since', '') == web_page.getModificationDate().rfc822():
  response.setStatus(304)
  return ""

web_content = web_page.getTextContent()

web_content = web_page.TextDocument_substituteTextContent(web_content, mapping_dict={})

response.setHeader('Content-Type', 'text/plain')

return web_content
