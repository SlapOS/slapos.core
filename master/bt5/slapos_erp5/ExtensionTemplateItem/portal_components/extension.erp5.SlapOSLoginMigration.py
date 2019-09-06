def migrateInstanceToERP5Login(self):
  assert self.getPortalType() in ( 'Computer', 'Software Instance')

  reference = self.getReference()
  if not reference:
    # no user id and no login is required
    return
  if not (self.hasUserId() or self.getUserId() == reference):
    self.setUserId(reference)

  if len(self.objectValues(
      portal_type=["Certificate Login", "ERP5 Login"])):
    # already migrated
    return

  login = self.newContent(
    portal_type='Certificate Login',
    reference=reference,
  )

  login.validate()
