from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

return {
  "title": context.getCausalityTitle(),
  "text_content": context.getTextContent(),
  "link": context.getCausalityValue(context).getFollowUp(checked_permission='View')
}
