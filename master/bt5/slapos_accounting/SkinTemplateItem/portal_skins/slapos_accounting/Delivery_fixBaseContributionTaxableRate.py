from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

delivery = context
portal = context.getPortalObject()

# Sale case only for now
source_section_value = delivery.getSourceSectionValue(portal_type='Organisation')

if source_section_value is None:
  # Do not try to calculate the VAT if nobody is selling
  return

source_section_country = source_section_value.getDefaultAddressRegion('')
if source_section_country == 'europe/west/france':
  # Consider only Service case
  destination_section_value = delivery.getDestinationSectionValue()
  if destination_section_value is None:
    # If sold to nobody, no tax calculation is possible
    return

  destination_section_country = destination_section_value.getDefaultAddressRegion('')
  # https://entreprendre.service-public.fr/vosdroits/F37527
  if destination_section_country == 'europe/west/france':
    if (destination_section_value.getPortalType() == 'Person'):
      taxable_suffix = 'vat/normal_rate'
    elif (destination_section_value.getVatCode('') != ''):
      taxable_suffix = 'vat/normal_rate'
    else:
      return
  elif destination_section_country in [
    'europe/west/germany',
    'europe/west/austria',
    'europe/west/belgium',
    'europe/east/bulgariya',
    'asia/west/cyprus',
    'europe/south/croatia',
    'europe/north/denmark',
    'europe/south/spain',
    'europe/north/estonia'
    'europe/north/finland',
    'europe/south/greece',
    'europe/east/hungary',
    'europe/north/ireland',
    'europe/south/italy',
    'europe/north/lithuania',
    'europe/north/latvia',
    'europe/west/luxembourg',
    'europe/south/malta',
    'europe/west/netherlands',
    'europe/east/poland',
    'europe/south/portugal',
    'europe/east/czech_republic',
    'europe/east/romania',
    'europe/east/slovakia',
    'europe/south/slovenia',
    'europe/north/sweden',
  ]:
    if (destination_section_value.getPortalType() == 'Person'):
      taxable_suffix = 'vat/normal_rate'
    elif (destination_section_value.getVatCode('') != ''):
      taxable_suffix = 'vat/zero_rate'
    else:
      return
  elif destination_section_country != '':
    # World
    taxable_suffix = 'vat/zero_rate'
  else:
    # No country where we sold
    return
else:
  # Only implement a simple VAT calculation for France for now
  return



for line in delivery.contentValues(portal_type=portal.getPortalDeliveryMovementTypeList() + ('Open Sale Order Line', )):
  # XXX calculate tax
  contribution_list = line.getBaseContributionList()

  if 'base_amount/invoicing/taxable' in contribution_list:
    new_contribution_list = []
    for contribution in contribution_list:
      if contribution == 'base_amount/invoicing/taxable':
        contribution = 'base_amount/invoicing/taxable/' + taxable_suffix
      new_contribution_list.append(contribution)

    line.edit(base_contribution_list=new_contribution_list)
