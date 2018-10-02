note_weight = {
 'A' : 0,
 'B' : 1,
 'C' : 3,
 'D' : 5,
 'E' : 7,
 'F' : 9
}

note_label = {
 'A' : "GOOD",
 'B' : "OK",
 'C' : "WORK REQUIRED",
 'D' : "BAD",
 'E' : "REALLY BAD",
 'F' : "UNUSABLE"
}

grade_list= [
  ["closed_per_day", dict(month_avg=True, delta_closed_amount=True)],
  ["closed_per_day", dict(week_avg=True, delta_closed_amount=True)],
  ["closed_per_day", dict(delta=0, delta_closed_amount=True)],
  ["closed_per_day", dict(delta=-1, delta_closed_amount=True)],
  ["avg_created_per_day", dict(week_avg=True)],
  ["avg_created_per_day", dict(month_avg=True)],
  ["created_per_day", dict(delta=0)],
  ["created_per_day", dict(delta=-1)],
]

grade_result_list = []
for key, params in grade_list:
  grade_result_list.append(
    context.Base_getServiceLevelObjectGrade(key,
      context.SupportRequestModule_countTicket(**params)))

remaining_grade = context.Base_getServiceLevelObjectGrade("remaining_ticket",
      context.portal_catalog.countResults(portal_type="Support Request", simulation_state=["validated", "suspended"])[0][0])

# Remaining Grade has the double of the weight
grade_result_list.append(remaining_grade)
grade_result_list.append(remaining_grade)

result = 0
for grade_result in grade_result_list:
  result += note_weight[grade_result.split(" ")[0]]

for n, value in note_weight.iteritems():
  if result <= len(grade_result_list)*value:
    return "%s (%s)" % (note_label[n], n)

return "F (UNUSABLE)"
