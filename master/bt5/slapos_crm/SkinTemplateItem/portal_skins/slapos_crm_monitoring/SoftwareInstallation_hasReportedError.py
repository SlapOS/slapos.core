from DateTime import DateTime

d = context.getAccessStatus()
# Ignore if data isn't present.
if d.get("no_data", None) == 1:
  return

if d['text'].startswith('#error '):
  return DateTime(d.get('created_at'))
