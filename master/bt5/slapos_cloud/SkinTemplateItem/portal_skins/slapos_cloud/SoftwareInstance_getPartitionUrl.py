# Script to generate URL for computer partiton of Software Instances
# both for XHTML UI as well as renderJS UI
if brain is None:
  brain = context

# 'brain' in this case is the Software Instance, hence trying to get
# the partition as it it related to the Software Instance with 'aggregate'
# category, hence, this will get us the relative URL of the aggregate
aggregate_value = brain.getAggregateValue()
jio_key = aggregate_value.getRelativeUrl()

# Creating URL for the computer module partition object
url = aggregate_value.absolute_url()

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
