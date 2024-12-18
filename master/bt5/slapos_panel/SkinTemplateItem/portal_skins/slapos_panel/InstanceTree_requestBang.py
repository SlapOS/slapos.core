instance_tree = context

instance = ([x for x in instance_tree.getSuccessorValueList() if (x.getTitle() == instance_tree.getTitle()) and (x.getSlapState() != 'destroy_requested')] + [None])[0]
if (instance is None) or (instance.getSlapState() == 'destroy_requested'):
  return context.Base_redirect('view', keep_items={'portal_status_message':context.Base_translateString('No root instance to process.')})

instance.bang(
  comment='Force reprocess from panel',
  bang_tree=True
)
return instance_tree.Base_redirect('view', keep_items={'portal_status_message':context.Base_translateString('Reprocessing requested.')})
