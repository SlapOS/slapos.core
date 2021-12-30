from DateTime import DateTime

if context.getAggregateValue(portal_type="Compute Partition") is not None:
  d = context.getAccessStatus()
  # Ignore if data isn't present.
  if d.get("no_data", None) == 1:
    if include_message:
      return "Not possible to connect"
    return

  result = d['text']
  last_contact = DateTime(d.get('created_at'))
  since = DateTime(d.get('since'))

  if result.startswith('#error '):
    if ((DateTime()-since)*24*60) > tolerance:
      if include_created_at and not include_since:
        return result, last_contact
      elif include_created_at and include_since:
        return result, last_contact, since
      return result

  if include_message and include_created_at and not include_since:
    return result, last_contact
  elif include_message and include_created_at and include_since:
    return result, last_contact, since
  elif include_message and not include_created_at:
    return result

return None
