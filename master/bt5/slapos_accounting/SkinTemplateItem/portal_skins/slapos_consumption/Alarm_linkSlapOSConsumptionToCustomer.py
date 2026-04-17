portal = context.getPortalObject()
activate_kw = {'tag': tag}

# An order builder is used to group all packing list if they match the same customer/trade condition
portal.portal_orders.slapos_consumption_sale_packing_list_builder.build(activate_kw=activate_kw)

# register activity on alarm object waiting for own tag in order to have only one alarm
# running in same time
context.activate(after_tag=tag).getId()
