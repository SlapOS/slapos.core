if brain is None:
  brain = context

software_instance = brain.getAggregateRelatedValue(portal_type=["Software Instance"])
if software_instance is None:
  return None

hosting_subscription = software_instance.getSpecialiseValue()

if url_dict: # If RenderJS UI
  jio_key = hosting_subscription.getRelativeUrl()
  return {
    'command': 'push_history',
    'view_kw': {
      'view': 'view',
      'jio_key': jio_key,
    },
    'options': {
      'jio_key': jio_key
    },
  }
else:
  return hosting_subscription.absolute_url()
