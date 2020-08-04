grade = context.Base_getServiceLevelObjectGrade(slo, value)

return grade

# Report seems not able to render HTML
# color_dict = {
#  "A": "lightgreen",
#  "B": "green",
#  "C": "blue",
#  "D": "orange",
#  "E": "red",
#  "F": "red",
# }
# for g, color in color_dict.iteritems():
#   if grade.startswith(g):
#     return "<font color='%s'>%s</font>" % (color, grade)
