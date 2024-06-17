result = []
# Copied from EmailDocument_viewAttachmentListRenderer
for information in context.getAttachmentInformationList():
  if information['uid'] != information['filename']:
    result.append({
      'title': information['filename'] or information['uid'],
      'content_type': information['content_type'],
      'url': '%s/getAttachmentData?index:int=%s' % (context.absolute_url(), information['index'])
    })
return result
