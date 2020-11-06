for path, uid in column_list:
  try:
    ob = context.restrictedTraverse(path)
  except KeyError:
    context.log("object not found", path)
    context.portal_catalog.activate(activity='SQLQueue').uncatalog_object(uid=uid)
  else:
    ob.reindexObject()
