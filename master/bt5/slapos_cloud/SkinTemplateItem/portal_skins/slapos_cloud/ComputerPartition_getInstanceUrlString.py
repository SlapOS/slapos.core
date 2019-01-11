if brain is None:
  brain = context

software_instance = brain.getAggregateRelatedValue(portal_type=["Software Instance"])
jio_key = software_instance.getRelativeUrl()

url = software_instance.absolute_url()

if url_dict:
  return {
    'command': 'push_history',
    'view_kw': {
      'view': 'view',
      'jio_key': jio_key,
    },
    'options': {
      'jio_key': jio_key
          }
         }

return url
