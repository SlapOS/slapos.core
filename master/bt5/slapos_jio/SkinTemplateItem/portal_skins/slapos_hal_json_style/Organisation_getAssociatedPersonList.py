from Products.ERP5Type.Document import newTempBase

temp_object_list = []
for assignment in context.getDestinationRelatedValueList(portal_type="Assignment"):
  person = assignment.getParentValue()
  temp_object_list.append(
    newTempBase(
      context, str(person.getId()),
      title=person.getTitle(),
      default_email_text=person.getDefaultEmailText()
    )
  )
return temp_object_list
