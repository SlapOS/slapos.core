from Products.ERP5Type.Cache import CachingMethod
if REQUEST is None:
  REQUEST = context.REQUEST
if response is None:
  response = REQUEST.RESPONSE

default_web_page = context
web_section = REQUEST.get("current_web_section")

return default_web_page.WebPage_viewAsWeb(mapping_dict={
    "frontpage_gadget": web_section.getLayoutProperty("configuration_frontpage_gadget_url", default=""),
    "application_title": web_section.getLayoutProperty("configuration_application_title", default="ERP5"),
    "action_view": web_section.getLayoutProperty("configuration_view_action_category", default="object_view"),
    "default_view_reference": web_section.getLayoutProperty("configuration_default_view_action_reference", default="view"),
    "hateoas_url": web_section.getLayoutProperty("configuration_hateoas_url", default="hateoas/"),
    "panel_gadget": web_section.getLayoutProperty("configuration_panel_gadget_url", default="gadget_erp5_panel.html"),
    "jio_gadget": web_section.getLayoutProperty("configuration_jio_gadget_url", default="gadget_jio.html"),
    "manifest_url": web_section.getLayoutProperty("configuration_manifest_url", default="gadget_erp5.appcache"),
    "javascript_main_code" : web_section.getDocumentValue("gadget_cdn_selector.js").getData(),
    "rsvp_code" : web_section.getDocumentValue("rsvp.js").getData()
  })
