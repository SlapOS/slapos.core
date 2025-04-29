data_dict['portal_type'] = 'Software Instance'
instance = context.JSONRPCService_getObjectFromData(data_dict)

if data_dict["title"] != instance.getTitle():
  instance.rename(
    new_name=data_dict["title"],
    comment="Rename %s into %s" % (instance.getTitle(), data_dict["title"])
  )

return {
  "title": "Title updated",
  "type": "success"
}
