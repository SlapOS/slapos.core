if context.getDelivery() is not None:
  # movement build but not indexed, so do nothing
  return
if context.getLedger() != 'automated':
  return

# group by specialise: the trade condition is the common link betweek every line/cell on a delivery

business_link = context.getCausalityValue(portal_type='Business Link')
if business_link is None:
  raise ValueError('Movement without business link: %s' % context.getRelativeUrl())

trade_condition = context.getSpecialiseValue()
if trade_condition is None:
  raise ValueError('Movement without specialise: %s' % context.getRelativeUrl())

lock_tag = 'build_in_progress_%s_%s' % (business_link.getUid(), trade_condition.getUid())
if context.getPortalObject().portal_activities.countMessageWithTag(lock_tag) == 0:
  #trade_condition.serialize()
  business_link.build(
    ledger__uid=context.getPortalObject().portal_categories.ledger.automated.getUid(),
    specialise__uid=trade_condition.getUid(),
    activate_kw={'tag': tag}
  )
  business_link.activate(activity='SQLQueue', after_tag=tag, tag=lock_tag).getId()
else:
  # Wait for the previous run to be finished, and try to build the movement again
  context.activate(activity='SQLQueue', after_tag=lock_tag).Base_reindexAndSenseAlarm(['slapos_trigger_build'], must_reindex_context=False)
