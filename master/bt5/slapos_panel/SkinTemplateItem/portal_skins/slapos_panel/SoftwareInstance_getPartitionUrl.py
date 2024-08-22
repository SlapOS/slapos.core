# Script to generate URL for compute_node partiton of Software Instances
# both for XHTML UI as well as renderJS UI
if brain is None:
  brain = context

# 'brain' in this case is the Software Instance, hence trying to get
# the partition as it it related to the Software Instance with 'aggregate'
# category, hence, this will get us the relative URL of the aggregate
partition = brain.getAggregateValue()
if partition is None:
  return None

if url_dict: # if RenderJS UI
  jio_key = partition.getRelativeUrl()
  return {
    'command': 'push_history',
    'view_kw': {
      'view': 'slapos_panel_view',
      'jio_key': jio_key,
    },
    'options': {
      'jio_key': jio_key
    },
  }
else:
  return partition.absolute_url()
