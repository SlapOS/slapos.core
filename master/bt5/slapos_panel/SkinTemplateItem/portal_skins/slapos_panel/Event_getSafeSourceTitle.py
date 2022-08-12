return context.getSourceTitle(checked_permission='View') or context.getSourceProjectTitle(checked_permission='View') or context.getFollowUpTitle(checked_permission='View') or None
