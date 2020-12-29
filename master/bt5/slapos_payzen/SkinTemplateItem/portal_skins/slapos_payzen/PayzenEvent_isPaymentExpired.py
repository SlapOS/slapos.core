"""
  This script was introduced for backward compatibility on migration and for 
  introduce custom delays on what configures the expiration dates.
"""

from DateTime import DateTime
return int(DateTime()) - int(transaction_date) > 86400
