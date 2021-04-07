portal = context.getPortalObject()
url_string = context.getUrlString()
image_url = ""

release = portal.portal_catalog.getResultValue(
    portal_type="Software Release",
    url_string=url_string,
)
if release is not None:
  software_product = release.getAggregateValue()
  # set default value of image_url to the panel's logo 
  image_url = software_product.getDefaultImageAbsoluteUrl() or "gadget_slapos_panel.png"

return image_url
