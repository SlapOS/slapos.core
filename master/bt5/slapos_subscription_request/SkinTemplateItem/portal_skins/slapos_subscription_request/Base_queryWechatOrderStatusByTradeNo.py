if not trade_no:
  raise Exception("Unknown trade number")

return context.Base_queryWechatOrderStatus({'out_trade_no': trade_no})
