mapping_dict = {}

url_map = {"deploy-Function.Common" : "function_common_content",
       "deploy-Base.Setup": "base_setup_content",
       "deploy-Vifib.Channel": "slapos_install_content",
       "deploy-Testing.Channel": "slapos_testing_content",
       "deploy-Unstable.Channel": "slapos_unstable_content"}

portal = context.getPortalObject()
for doc in portal.portal_catalog(reference=url_map.keys(),
                                    portal_type="Web Page",
                                    validation_state=["published", "published_alive"]):

  mapping_dict[url_map[doc.getReference()]] = doc.getTextContent()

return mapping_dict
