# Update the document id to be commited

if not context.getId().startswith("202"):
  raise ValueError("already updated")

if context.getValidationState() not in ["published", "published_alive" ]:
  raise ValueError("Not published yet, please publish the document first")

reference = context.getReference()
if reference is None:
  raise ValueError("Reference is None")

new_id = "rjs_" + reference.replace(".", "_")
context.setId(new_id)

return context.getRelativeUrl()
