portal = context.getPortalObject()
from Products.ERP5Type.Document import newTempBase

kw = {}
kw["portal_type"] = "Instance Tree"
kw["validation_state"] = "validated"
#kw["url_string"] = ["%%/software/slaprunner/software.cfg", "%%/software/kvm/software.cfg"]
kw["select_list"] = ["url_string", "source_reference"]

def getIndex(instance_tree):
  if "software/slaprunner/software.cfg" in instance_tree.url_string:
    if "resilient" == instance_tree.source_reference:
      return "webrunner_resilient"
    else:
      return "webrunner_non_resilient"
  elif "software/kvm/software.cfg" in instance_tree.url_string:
    if "resilient" in instance_tree.source_reference:
      return "kvm_resilient"
    else:
      return "kvm_non_resilient"

  return "other_type"

l = {}
for instance_tree in context.portal_catalog(**kw):
  u = instance_tree.getDestinationSection()
  if u not in l:
    l[u] = {"webrunner_resilient": 0,
            "webrunner_non_resilient": 0,
            "kvm_resilient": 0,
            "kvm_non_resilient": 0,
            "other_type": 0,
            "user_total": 0}
  index = getIndex(instance_tree)
  l[u][index] = l[u][index] + 1
  l[u]["user_total"] = l[u]["user_total"] + 1

document_list = []
for person_relative_url in l:
  person = portal.restrictedTraverse(person_relative_url)
  document_list.append(
    newTempBase(context.person_module, person.getId(),
      uid = "t_%s" % person.getUid(), title=person.getTitle(),
      **l[person_relative_url]))

document_list.sort(key=lambda obj: obj.user_total, reverse=True)

return document_list
