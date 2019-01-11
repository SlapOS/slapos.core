if brain is None:
  brain = context

instance = brain.getAggregateRelatedValue(portal_type=["Software Instance", "Slave Instance"])
owner = instance.getSpecialiseValue().getDestinationSectionValue()
jio_key = owner.getRelativeUrl()

url = owner.absolute_url()

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
