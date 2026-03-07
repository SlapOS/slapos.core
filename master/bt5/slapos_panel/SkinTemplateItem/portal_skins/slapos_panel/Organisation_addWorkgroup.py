organisation = context
portal = context.getPortalObject()
translate = portal.Base_translateString

assert organisation.getPortalType() == "Organisation"
if organisation.getVatCode('') == '':
  return organisation.Base_redirect(
    'view',
    keep_items={
      'portal_status_level': 'error',
      'portal_status_message': translate('Please fill VAT Code before create an Workgroup.'),
    }
  )

workgroup = portal.workgroup_module.newContent(
  portal_type='Workgroup',
  title=title,
  # This destination section is used whenever we generate a
  # Sale Trade Condition.
  destination_section_value=organisation,
  activate_kw=activate_kw
)

if len(workgroup.checkConsistency()) != 0:
  raise AssertionError(workgroup.checkConsistency()[0])

workgroup.validate(comment='Created by %s' % organisation.getRelativeUrl())
if batch:
  return workgroup

return workgroup.Base_redirect(
  'view',
  keep_items={
    'portal_status_message': translate('Workgroup created.'),
  }
)
