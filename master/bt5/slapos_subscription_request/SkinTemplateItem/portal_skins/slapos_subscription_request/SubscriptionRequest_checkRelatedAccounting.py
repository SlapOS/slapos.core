subscription_request = context
portal = context.getPortalObject()
translate = portal.Base_translateString
status_list = []

def addToStatusList(status_text, mapping):
  status_list.append(translate(
    status_text,
    mapping=mapping
  ))

if not context.getSimulationState() in ("ordered", "confirmed", "started", "stopped", "delivered"):
  return []

subscription_trade_condition = portal.sale_trade_condition_module.slapos_aggregated_subscription_trade_condition
#refund_service = portal.service_module.slapos_reservation_refund

sale_packing_list_list = portal.portal_catalog(
  portal_type="Sale Packing List",
  strict_causality_uid=subscription_request.getUid(),
  strict_destination_uid=subscription_request.getDestinationSectionUid(),
  strict_destination_section_uid=subscription_request.getDestinationSectionUid(),
  strict_specialise_uid=subscription_trade_condition.getUid(),
  simulation_state="delivered",
)

if sale_packing_list_list:
  sale_invoice_list = portal.portal_catalog(
    portal_type="Sale Invoice Transaction",
    strict_causality_uid=[x.getUid() for x in sale_packing_list_list],
  )
  subscription_currency = subscription_request.getPriceCurrency()
  for sale_invoice in sale_invoice_list:
    sale_invoice = sale_invoice.getObject()
    if sale_invoice.getPriceCurrency() != subscription_currency:
      addToStatusList(
        "${invoice_relative_url} Sale Invoice currency ${invoice_currency} do not match subscription currency ${subscription_currency}",
        {
          "invoice_relative_url": sale_invoice.getRelativeUrl(),
          "invoice_currency": sale_invoice.getPriceCurrency(),
          "subscription_currency": subscription_currency,
        }
      )

    if sale_invoice.getSimulationState() not in ("stopped", "delivered", "cancelled"):
      addToStatusList(
        "${invoice_relative_url} Sale Invoice in unexpected simulation state: ${invoice_simulation_state}",
        {
          "invoice_relative_url": sale_invoice.getRelativeUrl(),
          "invoice_simulation_state": sale_invoice.getSimulationState(),
        }
      )
return status_list
