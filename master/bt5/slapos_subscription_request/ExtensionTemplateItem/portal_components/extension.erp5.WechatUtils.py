import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# RapidSpace Wechat acocunt configuration

APP_ID = "";  # Wechat public account appid
MCH_ID = "";  # Wechat merchant account ID
API_KEY = "";  # Wechat merchant platform(pay.weixin.qq.com) -->账户设置 -->API安全 -->密钥设置

CREATE_IP = "";  # The IP address which request the order to Wechat, aka: instance IP
UFDODER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"; # Wechat unified order API
NOTIFY_URL = "your IP：port／Method";  # Wechat payment callback method


def getWechatQRCodeURL(self, order_id, price, amount):
  product_name = "Pre-order " + amount + " RapidSpace VM "
  return

  # TODO: waiting for the APP_ID
  appid = APP_ID
  mch_id = self._MCH_ID
  key = self._API_KEY
  # nonce_str = str(int(round(time.time() * 1000)))+str(random.randint(1,999))+string.join(random.sample(['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'], 5)).replace(" ","") #生成随机字符串
  nonce_str = ""
  spbill_create_ip = self._CREATE_IP
  notify_url = self._NOTIFY_URL
  trade_type = "NATIVE"

  # Construct parameter for calling the Wechat payment URL
  params = {}
  params['appid'] = appid
  params['mch_id'] = mch_id
  params['nonce_str'] = nonce_str
  params['out_trade_no'] = order_id.encode('utf-8')
  params['total_fee'] = amount   # unit is Fen, 1 CHY = 100 Fen
  params['spbill_create_ip'] = spbill_create_ip
  params['notify_url'] = notify_url
  params['body'] = product_name.encode('utf-8')
  params['trade_type'] = trade_type

  # generate signature
  ret = []
  for k in sorted(params.keys()):
    if (k != 'sign') and (k != '') and (params[k] is not None):
      ret.append('%s=%s' % (k, params[k]))
      params_str = '&'.join(ret)
      params_str = '%(params_str)s&key=%(partner_key)s'%{'params_str': params_str, 'partner_key': key}
      reload(sys)
      sys.setdefaultencoding('utf8')
      params_str = "" #hashlib.md5(params_str.encode('utf-8')).hexdigest()
      sign = params_str.upper()
      params['sign'] = sign

      # construct XML
      request_xml_str = '<xml>'
      for key, value in params.items():
        if isinstance(value, basestring):
          request_xml_str = '%s<%s><![CDATA[%s]]></%s>' % (request_xml_str, key, value, key, )
        else:
          request_xml_str = '%s<%s>%s</%s>' % (request_xml_str, key, value, key, )
      request_xml_str = '%s</xml>' % request_xml_str
'''
      # send data
      res = "" #urllib2.Request(self._UFDODER_URL, data=request_xml_str)
      res_data = "" #urllib2.urlopen(res)
      res_read = res_data.read()
      doc =  #xmltodict.parse(res_read)
      return_code = doc['xml']['return_code']
      if return_code=="SUCCESS":
        result_code = doc['xml']['result_code']
        if result_code=="SUCCESS":
          code_url = doc['xml']['code_url']
          return code_url
        else:
          err_des = doc['xml']['err_code_des']
          print "errdes==========="+err_des
      else:
        fail_des = doc['xml']['return_msg']
        print "fail des============="+fail_des
'''
