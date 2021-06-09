project = context.Item_getCurrentProjectValue(**kw)
if project is not None:
  return project.title
