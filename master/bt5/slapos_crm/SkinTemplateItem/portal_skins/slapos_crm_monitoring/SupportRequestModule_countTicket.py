from DateTime import DateTime

portal = context.getPortalObject()

# Hardcode the Date Range here
if month_avg:
  today = DateTime() - 30
  creation_date = ">=%s/%02d/%02d" % (today.year(), today.month(), today.day())
  ratio = 30
elif week_avg:
  today = DateTime() - 7
  creation_date = ">=%s/%02d/%02d" % (today.year(), today.month(), today.day())
  ratio = 7
else:
  ratio = 1
  today = DateTime() + delta
  creation_date = "%s/%02d/%02d" % (today.year(), today.month(), today.day())

def getSupportRequestList(creation_date):
  return portal.portal_catalog(
    portal_type="Support Request",
    creation_date=creation_date)

def getClosedSupportRequestList(modifiction_date):
  return portal.portal_catalog(
    portal_type="Support Request",
    simulation_state="invalidated",
    modification_date=modifiction_date)

if delta_closed_amount:
  return (len(getSupportRequestList(creation_date)) - len(getClosedSupportRequestList(creation_date)))/ratio

return len(getSupportRequestList(creation_date))/ratio
