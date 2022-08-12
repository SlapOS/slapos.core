from Products.ERP5Type.Message import translateString
request = context.REQUEST

try:
  context.generateCertificate()
except ValueError:
  message = "This compute_node already has one certificate, please revoke it before request a new one.."
  status = 'warning'
  return context.Base_redirect(
    keep_items={
      'portal_status_message': translateString(message),
      'portal_status_level': status
    }
  )
else:
  message = "Certificate is Requested."
  status = 'success'
  return context.Base_renderForm(
    'Base_viewSlapOSComputeNodeCertificateDialog',
    message=translateString(message),
    level=status,
    keep_items={
      'your_compute_node_certificate': request.get('compute_node_certificate'),
      'your_compute_node_key': request.get('compute_node_key'),
      'your_compute_node_reference': context.getReference(),
      'your_compute_node_relative_url': context.getRelativeUrl()
    }
  )
