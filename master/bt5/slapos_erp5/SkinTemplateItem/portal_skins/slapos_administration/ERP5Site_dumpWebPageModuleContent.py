import hashlib
portal = context.getPortalObject()

if not ignore_string_on_reference_list:
  ignore_string_on_reference_list = []

def getWebContentHash(document):
  content = document.getTextContent("ignore")
  m = hashlib.md5()
  m.update(content)
  content_hash = m.hexdigest()
  return ";".join((document.getReference(), content_hash))

zero_to_nine_list = range(10)

for document in portal.web_page_module.searchFolder(
    validation_state=["published", "published_alive"]):

  document_id_first_letter = document.getId()[0]
  if document_id_first_letter in zero_to_nine_list:
    continue

  print_web_content = 1
  document_reference = str(document.getReference(""))
  for ignore_string in ignore_string_on_reference_list:
    if ignore_string in document_reference:
      print_web_content = 0
      break

  if print_web_content:
    print(getWebContentHash(document))

container.REQUEST.RESPONSE.setHeader('content-type', 'text/plain')
return '\n'.join(sorted(printed.splitlines()))
