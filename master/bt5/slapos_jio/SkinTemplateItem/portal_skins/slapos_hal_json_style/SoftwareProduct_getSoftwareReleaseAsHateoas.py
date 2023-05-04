import json

software_release_relative_url = ""

kw = {
  "software_release_url" : software_release,
  "strict": strict
}
if software_release.startswith("product."):
  kw = {"software_product_reference": software_release[8:]}

software_release_list = context.SoftwareProduct_getSortedSoftwareReleaseList(**kw)
if len(software_release_list):
  software_release_relative_url = software_release_list[0].getRelativeUrl()

return json.dumps(software_release_relative_url)
