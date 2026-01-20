"""
Generic method called when submitting a form in dialog mode.
Responsible for validating form data and redirecting to the form action.
"""
from zExceptions import Unauthorized
if REQUEST is None:
  raise Unauthorized

from Products.Formulator.Errors import FormValidationError

request = REQUEST
request_form = request.form

# Make this script work alike wether called from another script or by a request
kw.update(request_form)
kw = {}

form = getattr(context, dialog_id)

# Validate the form
try:
  # It is necessary to force editable_mode before validating
  # data. Otherwise, field appears as non editable.
  # This is the pending of form_dialog.
  editable_mode = request.get('editable_mode', 1)
  request.set('editable_mode', 1)
  form.validate_all_to_request(request)
  request.set('editable_mode', editable_mode)
except FormValidationError as validation_errors:
  # Pack errors into the request
  field_errors = form.ErrorFields(validation_errors)
  request.set('field_errors', field_errors)
  return form(request)

MARKER = [] # A recognisable default value. Use with 'is', not '=='.
for field in form.get_fields():
  k = field.id
  v = request.get(k, MARKER)
  if v is not MARKER:

    # Cleanup my_ and your_ prefixes
    splitted = k.split('_', 1)
    if len(splitted) == 2 and splitted[0] in ('my', 'your'):

      if hasattr(v, 'as_dict'):
        # This is an encapsulated editor
        # convert it
        kw.update(v.as_dict())
      else:
        kw[splitted[1]] = request_form[splitted[1]] = v

    else:
      kw[k] = request_form[k] = v

# Remove values which doesn't work with make_query.
clean_kw = {}
for k, v in kw.items() :
  if v not in (None, [], ()) :
    clean_kw[k] = kw[k]

for key in list(request.form.keys()):
  if str(key).startswith('field') or str(key).startswith('subfield'):
    request.form.pop(key, None)

# call the form directly.
dialog_form = getattr(context, dialog_method)
return dialog_form(dialog_id=dialog_id, **clean_kw)


# vim: syntax=python
