if brain is None:
  brain = context

if brain.getPortalType() == "Instance Tree":
  url = '%s/InstanceTree_redirectToManualDepositPayment' % brain.absolute_url()
else:
  url = '%s/Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect' % brain.absolute_url()

if url_dict:
  return {'command': 'raw',
          'options': {
            'url': url
            }
    }
return url
