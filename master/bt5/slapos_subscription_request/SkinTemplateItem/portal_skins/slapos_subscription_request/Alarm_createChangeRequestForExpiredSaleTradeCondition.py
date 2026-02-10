from Products.ZSQLCatalog.SQLCatalog import SimpleQuery

portal = context.getPortalObject()
ledger_uid = portal.portal_categories.ledger.automated.getUid()
activate_kw = {'tag': tag, 'priority': 5}

trade_condition_list = portal.portal_catalog(
  portal_type='Sale Trade Condition',
  validation_state='validated',
  **{'predicate.start_date_range_max': SimpleQuery(
    comparison_operator='<=',
    **{'predicate.start_date_range_max': DateTime()}
  )}
)
trade_condition_uid_list = [x.uid for x in trade_condition_list] or [-1]

portal.portal_catalog.searchAndActivate(
  portal_type='Sale Trade Condition',
  validation_state='validated',
  expiration_date=None,
  specialise__uid=trade_condition_uid_list,

  method_id='SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)

portal.portal_catalog.searchAndActivate(
  portal_type='Open Sale Order',
  ledger__uid=ledger_uid,
  validation_state='validated',
  expiration_date=None,
  specialise__uid=trade_condition_uid_list,

  method_id='OpenSaleOrder_generateSubscriptionChangeRequestFromExpiredSaleTradeCondition',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)

context.activate(after_tag=tag).getId()
