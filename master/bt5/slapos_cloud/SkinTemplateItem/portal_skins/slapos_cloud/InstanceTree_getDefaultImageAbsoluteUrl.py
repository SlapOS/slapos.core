# set default value of image_url to the panel's logo
image_url = "gadget_slapos_panel.png"

software_product, _, _ = context.InstanceTree_getSoftwareProduct()

if software_product is not None:
  product_image_url = software_product.getDefaultImageAbsoluteUrl()
  if product_image_url:
    image_url = product_image_url

return image_url
