portal = context.getPortalObject()
image_url = ""
url_string = context.getUrlString()

release = portal.portal_catalog.getResultValue(
    portal_type="Software Release",
    url_string=url_string,
)
if release is not None:
  software_product = release.getAggregateValue()
  image_url = '%s/index_html' % software_product.getDefaultImageAbsoluteUrl()

return image_url
