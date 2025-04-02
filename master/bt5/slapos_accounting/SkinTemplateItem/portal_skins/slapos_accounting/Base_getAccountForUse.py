'''
  Script to be used as API whenever we want to get an account for a
  specific use. Returns the Account object
'''

account_id = {
  'asset_receivable_subscriber': 'receivable',
  'asset_deposit_subscriber': 'deposit_received',
  'collection': 'payment_to_encash',
  'payable': 'payable',
  'suspense': 'suspense'
}[use]

account, = context.getPortalObject().portal_catalog(
  portal_type='Account',
  id=account_id,
  validation_state='validated',
  limit=2,
)

return account.getObject()
