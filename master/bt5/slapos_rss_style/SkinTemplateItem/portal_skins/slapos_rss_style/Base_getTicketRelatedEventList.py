return context.Base_getEventList(
  list_lines=list_lines,
  follow_up_portal_type=['Support Request', 'Upgrade Decision'],
  context_related=True, **kw)
