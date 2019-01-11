if brain is None:
  brain = context

jio_key = brain.getRelativeUrl()

url = '%s/Item_viewTrackingList?current:int=0' % (brain.absolute_url())

if url_dict:
  return {
    'command': 'push_history',
    'view_kw': {
      'view': 'Item_viewTrackingList',
      'jio_key': jio_key,
    },
    'options': {
      'jio_key': jio_key
    },
  }

return url
