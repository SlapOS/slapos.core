url = context.absolute_url() + "/SaleInvoiceTransaction_viewSlapOSPrintout"

if url_dict:
  return {
    'command': 'raw',
    'options': {
      'url': url
    }
  }

return url
