from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
project = context

def calculateSoftwareProductTitle(software_release_url):
  if not software_release_url.startswith('http'):
    return software_release_url

  try:
    result = software_release_url.split('/')[-2]
  except IndexError:
    result = software_release_url

  if not software_release_url.endswith('software.cfg'):
    result += ' %s' % software_release_url.split('/')[-1]
  return result

soft_dict = {}

###########################################################
# First, calculate the list of product by checking the instances
###########################################################
group_by_list = ["url_string", "follow_up__uid", "source_reference"]
sql_result_list = portal.portal_catalog(
  portal_type=["Software Instance", "Slave Instance"],
  follow_up__uid=project.getUid()
)

for sql_result in sql_result_list:

  if sql_result.getSlapState() in ["start_requested", "stop_requested"]:
    software_release_url = sql_result.getUrlString()
    software_product_title = calculateSoftwareProductTitle(software_release_url)
    if software_product_title not in soft_dict:
      soft_dict[software_product_title] = {
        'release_list': [],
        'type_list': []
      }
    soft_dict[software_product_title]['release_list'].append(software_release_url)
    soft_dict[software_product_title]['type_list'].append(sql_result.getSourceReference())

###########################################################
# Second, get info from all installed softwares
###########################################################
group_by_list = ["url_string", "follow_up__uid"]
sql_result_list = portal.portal_catalog(
  select_list=group_by_list,
  portal_type="Software Installation",
  slap_state=["start_requested"],
  follow_up__uid=project.getUid(),
  group_by=group_by_list,
)

for sql_result in sql_result_list:
  compute_node = sql_result.getAggregateValue()
  if (compute_node is not None) and (compute_node.getAllocationScope() == 'open'):

    software_release_url = sql_result['url_string']
    software_product_title = calculateSoftwareProductTitle(software_release_url)
    if software_product_title not in soft_dict:
      soft_dict[software_product_title] = {
        'release_list': [],
        'type_list': []
      }
    soft_dict[software_product_title]['release_list'].append(software_release_url)

###########################################################
# Create needed Software Product
###########################################################
for soft, variation_dict in soft_dict.items():

  software_product = portal.portal_catalog.getResultValue(
    portal_type="Software Product",
    title={'query': soft, 'key': 'ExactMatch'},
    follow_up__uid=project.getUid()
  )
  if software_product is None:
    software_product = portal.software_product_module.newContent(
      portal_type="Software Product",
      title=soft,
      follow_up_value=project,
      activate_kw=activate_kw
    )
    software_product.validate()

  for software_type in list(set(variation_dict['type_list'])):
    type_variation = portal.portal_catalog.getResultValue(
      portal_type="Software Product Type Variation",
      title={'query': software_type, 'key': 'ExactMatch'},
      parent_uid=software_product.getUid()
    )
    if type_variation is None:
      software_product.newContent(
        portal_type="Software Product Type Variation",
        title=software_type,
        activate_kw=activate_kw
      )

  release_list = list(set(variation_dict['release_list']))
  release_list.sort()
  for software_release in release_list:
    software_release_variation = portal.portal_catalog.getResultValue(
      portal_type="Software Product Release Variation",
      url_string={'query': software_release, 'key': 'ExactMatch'},
      parent_uid=software_product.getUid()
    )
    if software_release_variation is None:
      software_product.newContent(
        portal_type="Software Product Release Variation",
        title=software_release,
        url_string=software_release,
        activate_kw=activate_kw
      )
