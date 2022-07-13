portal = context.getPortalObject()
url_string = context.getUrlString()
# set default value of image_url to the panel's logo
image_url = "gadget_slapos_panel.png"

release = portal.portal_catalog.getResultValue(
    portal_type="Software Release",
    url_string=url_string,
)
if release is not None:
  software_product = release.getAggregateValue(
    checked_permission='Access contents information')
  if software_product is not None:
    image_url = software_product.getDefaultImageAbsoluteUrl()

return image_url
