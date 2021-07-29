from erp5.component.module.DateUtils import addToDate, getClosestDate
instance_tree = state_change['object']

edit_kw = {}

if instance_tree.getPeriodicityHour() is None:
  edit_kw['periodicity_hour_list'] = [0]
if instance_tree.getPeriodicityMinute() is None:
  edit_kw['periodicity_minute_list'] = [0]
if instance_tree.getPeriodicityMonthDay() is None:
  start_date = instance_tree.InstanceTree_calculateSubscriptionStartDate()
  start_date = getClosestDate(target_date=start_date, precision='day')
  while start_date.day() >= 29:
    start_date = addToDate(start_date, to_add={'day': -1})
  edit_kw['periodicity_month_day_list'] = [start_date.day()]

if edit_kw:
  instance_tree.edit(**edit_kw)
