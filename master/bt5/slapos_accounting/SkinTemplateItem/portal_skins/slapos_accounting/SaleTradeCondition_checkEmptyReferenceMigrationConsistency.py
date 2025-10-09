reference = context.getReference()

error_list = []

if reference:
  title = context.getTitle()
  if title != reference:
    return ['Error: Sale Trade Condition has both title and reference']

  error_list.append('Sale Trade Condition reference has not yet been migrated')
  if fixit:
    context.setReference(None)
    context.edit(title=title)
    assert not context.getReference()

return error_list
