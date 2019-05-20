if context.getPortalType() != "Notification Message Module":
  raise ValueError("This folder is not a Notification Message Module")

for notification_message in context.searchFolder(id="201%", validation_state="validated"):
  if notification_message.getValidationState() != 'validated':
    continue

  new_id = "master_prod_%s_%s_%s" % (notification_message.getReference().replace("-", "_").replace(".", "_"),
                                     notification_message.getLanguage("en"),
                                     notification_message.getVersion("001"))
  notification_message.getObject().setId(new_id)
