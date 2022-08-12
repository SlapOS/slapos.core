context.getAggregateValue(portal_type='Compute Node').requestSoftwareRelease(software_release_url=context.getUrlString(), state='destroyed')
return context.Base_redirect('view', keep_items={'portal_status_message': 'Requested Destruction'})
