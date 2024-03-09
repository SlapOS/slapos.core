from erp5.component.test.testHalJsonStyle import ERP5HALJSONStyleSkinsMixin, simulate, changeSkin, do_fake_request
import json

class TestSlapOSHalRestrictedCompatibility(ERP5HALJSONStyleSkinsMixin):
  def getHatoasWebSite(self):
    return self.portal.web_site_module.slapos_hateoas

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/bar"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('SlapOSHalRestricted')
  def test_restricted_mode_search(self):
    fake_request = do_fake_request("GET")
    self.logout()
    self.getHatoasWebSite().ERP5Document_getHateoas(REQUEST=fake_request, mode="search")
    self.assertEqual(fake_request.RESPONSE.status, 401)
    self.assertEqual(fake_request.RESPONSE.getHeader('WWW-Authenticate'),
      'X-Delegate uri="%s/connection/login_form{?came_from}"' % self.getHatoasWebSite().absolute_url()
    )

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/bar"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('SlapOSHalRestricted')
  def test_mode_search_rewrite_hosting_subscription(self):
    fake_request = do_fake_request("GET")
    result = self.getHatoasWebSite().ERP5Document_getHateoas(
      REQUEST=fake_request,
      mode="search",
      query='portal_type: "Hosting Subscription"'
    )

    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )
    result_dict = json.loads(result)
    self.assertEqual(result_dict['_query'].encode(),
                     'portal_type: "Instance Tree"')