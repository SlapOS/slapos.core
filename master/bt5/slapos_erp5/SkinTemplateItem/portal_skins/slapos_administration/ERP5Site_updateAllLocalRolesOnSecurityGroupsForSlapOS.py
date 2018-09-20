portal = context.getPortalObject()

# List of all portal types which contains some upgrade

for portal_type in ("Access Token Module" ,"Account Module" ,"Account" ,"Accounting Period" ,"Accounting Transaction Module" ,"Accounting Transaction" ,"Acknowledgement" ,"Assignment" ,"Balance Transaction" ,"Bank Account" ,"Computer", "Computer Partition", "Business Process Module" ,"Business Process" ,"Campaign Module" ,"Campaign" ,"Cash Register" ,"Cloud Contract Module" ,"Cloud Contract" ,"Component Module" ,"Component" ,"Computer Consumption TioXML File" ,"Computer Model Module" ,"Computer Model" ,"Computer Module" ,"Computer Network Module" ,"Computer Network" ,"Consumption Document Module" ,"Contribution Tool" ,"Credential Update Module" ,"Credit Card" ,"Currency Module" ,"Currency" ,"Data Set Module" ,"Data Set" ,"Document Ingestion Module" ,"Document Module" ,"Drawing" ,"Event Module" ,"Fax Message" ,"File" ,"Gadget Tool" ,"Gadget" ,"Hosting Subscription Module" ,"Hosting Subscription" ,"Image Module" ,"Image" ,"Integration Site" ,"Integration Tool" ,"Inventory Module" ,"Inventory" ,"Knowledge Box" ,"Knowledge Pad Module" ,"Knowledge Pad" ,"Letter" ,"Mail Message" ,"Meeting Module" ,"Meeting" ,"Note" ,"Notification Message Module" ,"Notification Message" ,"One Time Restricted Access Token" ,"Open Sale Order Module" ,"Open Sale Order" ,"Organisation Module" ,"Organisation" ,"PDF" ,"Payment Transaction" ,"Payzen Event" ,"Person Module" ,"Person" ,"Phone Call" ,"Presentation" ,"Product Module" ,"Product" ,"Project Module" ,"Project" ,"Purchase Invoice Transaction" ,"Purchase Order Module" ,"Purchase Order" ,"Purchase Trade Condition Module" ,"Purchase Trade Condition" ,"Query Module" ,"Query" ,"Regularisation Request Module" ,"Regularisation Request" ,"Restricted Access Token" ,"Sale Invoice Transaction" ,"Sale Opportunity Module" ,"Sale Opportunity" ,"Sale Order Module" ,"Sale Order" ,"Sale Packing List Module" ,"Sale Trade Condition Module" ,"Sale Trade Condition" ,"Service Module" ,"Service" ,"Short Message" ,"Site Message" ,"Slave Instance" ,"Software Installation Module" ,"Software Installation" ,"Software Instance Module" ,"Software Instance" ,"Software Product Module" ,"Software Product" ,"Software Release Module" ,"Software Release" ,"Spreadsheet" ,"Support Request Module" ,"Support Request" ,"System Event Module" ,"Text" ,"Transformation Module" ,"Transformation" ,"Upgrade Decision Module" ,"Upgrade Decision" ,"User Consumption HTML File" ,"Visit" ,"Web Message" ,"Web Page Module" ,"Web Page"):

  print portal_type
  portal.portal_types[portal_type].updateRoleMapping(priority=4)

context.portal_catalog.searchAndActivate(
  method_id="updateLocalRolesOnSecurityGroups",
  default_specialise_uid = [context.sale_trade_condition_module.slapos_subscription_trade_condition.getUid(),
                             context.sale_trade_condition_module.slapos_aggregated_trade_condition.getUid()],
  portal_type="Sale Packing List")

return printed
