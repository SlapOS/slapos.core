data_dict['portal_type'] = 'Software Instance'
instance = context.JSONRPCService_getObjectFromData(data_dict)

instance.setErrorStatus('bang called')
timestamp = str(int(instance.getModificationDate()))
key = "%s_bangstamp" % instance.getReference()

if not instance.isLastData(key, timestamp):
  instance.bang(bang_tree=True, comment=data_dict.get("message", ""))

return {
  "title": "Bang handled",
  "type": "success"
}
