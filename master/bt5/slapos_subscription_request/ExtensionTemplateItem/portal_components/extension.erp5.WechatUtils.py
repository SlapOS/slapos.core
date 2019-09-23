import sys
import random, string, hashlib, urllib2
try:
  import xml.etree.cElementTree as ET
except ImportError:
  import xml.etree.ElementTree as ET

reload(sys)
sys.setdefaultencoding('utf-8')

# RapidSpace Wechat acocunt configuration

APP_ID = ""  # Wechat public account appid
MCH_ID = ""  # Wechat merchant account ID
API_KEY = ""  # Wechat merchant platform(pay.weixin.qq.com) -->账户设置 -->API安全 -->密钥设置

CREATE_IP = ""  # The IP address which request the order to Wechat, aka: instance IP
UFDODER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder" # Wechat unified order API
NOTIFY_URL = "your IP: port/Method"  # Wechat payment callback method


def generateRandomStr(random_length=24):
  alpha_num = string.ascii_letters + string.digits
  random_str = ''.join(random.choice(alpha_num) for i in range(random_length))
  return random_str


def calculateSign(dict_content, key):
  # Calculate the sign according to the data_dict
  # The rule was defined by Wechat (Wrote in Chinese):
  # https://pay.weixin.qq.com/wiki/doc/api/native.php?chapter=4_3

  # 1. Sort it by dict order
  params_list = sorted(dict_content.items(), key=lambda e: e[0], reverse=False)
  # 2. Concatenate the list to a string
  params_str = "&".join(u"{}={}".format(k, v) for k, v in params_list)
  # 3. Add trade key in the end
  params_str = params_str + '&key=' + key

  md5 = hashlib.md5()  # Use MD5 mode
  md5.update(params_str.encode('utf-8'))
  sign = md5.hexdigest().upper()
  return sign


def convert_xml_to_dict(xml_content):
  '''
  The XML returned by Wechat is like:
    <xml>
       <return_code><![CDATA[SUCCESS]]></return_code>
       <return_msg><![CDATA[OK]]></return_msg>
       <appid><![CDATA[wx2421b1c4370ec43b]]></appid>
       <mch_id><![CDATA[10000100]]></mch_id>
       <nonce_str><![CDATA[IITRi8Iabbblz1Jc]]></nonce_str>
       <openid><![CDATA[oUpF8uMuAJO_M2pxb1Q9zNjWeS6o]]></openid>
       <sign><![CDATA[7921E432F65EB8ED0CE9755F0E86D72F]]></sign>
       <result_code><![CDATA[SUCCESS]]></result_code>
       <prepay_id><![CDATA[wx201411101639507cbf6ffd8b0779950874]]></prepay_id>
       <trade_type><![CDATA[JSAPI]]></trade_type>
    </xml>
  '''
  try:
    t = ET.XML(xml_content)
  except ET.ParseError:
    return {}
  else:
    dict_content = dict([(child.tag, child.text) for child in t])
    return dict_content


def convert_dict_to_xml(dict_content):
  dict_content['sign'] = calculateSign(dict_content, API_KEY)
  xml = ''
  for key, value in dict_content.items():
    xml += '<{0}>{1}</{0}>'.format(key, value)
  xml = '<xml>{0}</xml>'.format(xml)
  return xml


def getWechatQRCodeURL(self, order_id, price, amount):
  product_name = "Pre-order " + amount + " RapidSpace VM "
  return

  # TODO: waiting for the APP_ID
  appid = APP_ID # XXXXXXXXXXXXXXXXXXXXXXXXXXxx
  mch_id = MCH_ID
  key = API_KEY
  nonce_str = generateRandomStr()
  spbill_create_ip = CREATE_IP
  notify_url = NOTIFY_URL
  trade_type = "NATIVE"

  # Construct parameter for calling the Wechat payment URL
  params = {}
  params['appid'] = appid
  params['mch_id'] = mch_id
  params['nonce_str'] = nonce_str
  params['out_trade_no'] = order_id.encode('utf-8')
  params['total_fee'] = amount * 100   # unit is Fen, 1 CHY = 100 Fen
  params['spbill_create_ip'] = spbill_create_ip
  params['notify_url'] = notify_url
  params['body'] = product_name.encode('utf-8')
  params['trade_type'] = trade_type

  # generate signature
  params['sign'] = calculateSign(params, API_KEY)

  # construct XML str
  request_xml_str = '<xml>'
  for key, value in params.items():
    if isinstance(value, basestring):
      request_xml_str = '%s<%s><![CDATA[%s]]></%s>' % (request_xml_str, key, value, key, )
    else:
      request_xml_str = '%s<%s>%s</%s>' % (request_xml_str, key, value, key, )
  request_xml_str = '%s</xml>' % request_xml_str

  # send data
  result = urllib2.Request(UFDODER_URL, data=request_xml_str)
  result_data = urllib2.urlopen(result)
  result_read = result_data.read()
  result_dict_content = convert_xml_to_dict(result_read)
  return_code = result_dict_content['return_code']
  if return_code=="SUCCESS":
    result_code = result_dict_content['result_code']
    if result_code=="SUCCESS":
      code_url = result_dict_content['code_url']
      return code_url
    else:
      print("Error description: {0}".format(result_dict_content.get("err_code_des")))
  else:
    print("Error description: {0}".format(result_dict_content.get("return_msg")))


def receiveWechatPaymentNotify(self, request, *args, **kwargs):
  '''
  Receive the asychonized callback send by Wechat after user pay the order.
  Wechat will give us something like:
  <xml>
    <appid><![CDATA[wx6509f6e240dfae50]]></appid>
    <bank_type><![CDATA[CFT]]></bank_type>
    <cash_fee><![CDATA[1]]></cash_fee>
    <fee_type><![CDATA[CNY]]></fee_type>
    <is_subscribe><![CDATA[N]]></is_subscribe>
    <mch_id><![CDATA[14323929292]]></mch_id>
    <nonce_str><![CDATA[aCJv0SAwKY5Cxfi34mtCEM5SdNKexuXgnW]]></nonce_str>
    <openid><![CDATA[oHWl5w5M34hYM-ox2mn6Xatse7yCTs]]></openid>
    <out_trade_no><![CDATA[aHQDJyacUSGC]]></out_trade_no>
    <result_code><![CDATA[SUCCESS]]></result_code>
    <return_code><![CDATA[SUCCESS]]></return_code>
    <sign><![CDATA[C4F8B5B17A3E6203491A3B790A1D87ECEA]]></sign>
    <time_end><![CDATA[201712114144230]]></time_end>
    <total_fee>1</total_fee>
    <trade_type><![CDATA[NATIVE]]></trade_type>
    <transaction_id><![CDATA[4200000031201712112434025551875]]></transaction_id>
  </xml>
  '''
  params = convert_xml_to_dict(request.body)
  if params.get("return_code") == "SUCCESS":
    # Connection is ok
    sign = params.pop('sign')
    recalcualted_sign = calculateSign(params, API_KEY)
    if recalcualted_sign == sign:
      if params.get("result_code", None) == "SUCCESS":  # payment is ok
        # order number
        # out_trade_no = params.get("out_trade_no")
        # Wechat payment order ID
        # This is what we should use when we search the order in the wechat
        # transaction_id = params.get("out_trade_no")
        # We recevied the payment...
        # Process something
        # XXX: display the page the payment received.

        # We must tell Wechat we received the response. Otherwise wechat will keep send it within 24 hours
        # xml_str = convert_dict_to_xml({"return_code": "SUCCESS"})
        return True # HttpResponse(xml_str)
      else:
        print("{0}:{1}".format(params.get("err_code"), params.get("err_code_des")))
    else:
      # Error information
      print(params.get("return_msg").encode("utf-8"))
