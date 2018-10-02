slo_dict = context.ERP5Site_getServiceLevelObjectiveDict()

if slo not in slo_dict:
  raise ValueError("Service Level Objective not found!")

grade_dict = slo_dict[slo]

for grade, threshold  in grade_dict.iteritems():
  if value <= threshold:
    return "%s (%s)" % (grade, value)

return "F (%s)" % value
