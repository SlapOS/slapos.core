from DateTime import DateTime
from Products.ERP5Type.Document import newTempBase

portal = context.getPortalObject()

# Hardcode the Date Range here
today = DateTime()

date_set = set(["%s/%02d" % ((today-x).year(), (today-x).month()) for x in range(0,547, 27)])

def countDocument(creation_date, portal_type):
  return portal.portal_catalog.countResults(
    portal_type=portal_type,
    creation_date=creation_date)[0][0]

def countDocumentWithState(creation_date, portal_type):
  return portal.portal_catalog.countResults(
    portal_type=portal_type,
    validation_state="validated",
    creation_date=creation_date)[0][0]

def countInstanceWithState(creation_date, portal_type):
  hosting_subscription_uid_list = [hs.uid for hs in portal.portal_catalog(
    portal_type="Hosting Subscription",
    validation_state="validated",
    creation_date=creation_date)]


  return portal.portal_catalog.countResults(
    portal_type=portal_type,
    default_specialise_uid=hosting_subscription_uid_list)[0][0]


stats_list = []

creation_date_list = list(date_set)
creation_date_list.sort()

for creation_date in creation_date_list:     
  line = newTempBase(context, '%s' % creation_date.replace("/", "_"), **{
       "uid": "%s_%s" % (context.getUid(), len(stats_list)),
       "title": creation_date,
       "hosting_subscription_quantity" : countDocument(creation_date, "Hosting Subscription"),
       "hosting_subscription_residual" : countDocumentWithState(creation_date, "Hosting Subscription"),
       "instance_quantity": countInstanceWithState(creation_date, "Software Instance"),
       "slave_instance_quantity": countInstanceWithState(creation_date, "Slave Instance")})
  
  stats_list.append(line)

return stats_list
