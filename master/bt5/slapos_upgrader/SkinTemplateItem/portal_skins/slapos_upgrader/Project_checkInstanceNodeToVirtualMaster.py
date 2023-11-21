from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
project = context

group_by_list = ["aggregate__uid"]
sql_result_list = portal.portal_catalog(
  select_list=group_by_list,
  portal_type=["Slave Instance"],
  follow_up__uid=project.getUid(),
  group_by=group_by_list
)

for sql_result in sql_result_list:
  slave_instance = sql_result.getObject()

  partition = slave_instance.getAggregateValue()
  if (partition is not None) and (partition.getParentValue().getPortalType() == 'Compute Node'):
    instance_list = portal.portal_catalog(
      portal_type="Software Instance",
      aggregate__uid=partition.getUid(),
      limit=2
    )
    if (len(instance_list) == 1) and (instance_list[0].getSpecialise() != slave_instance.getSpecialise()):

      software_instance = instance_list[0]
      instance_tree = software_instance.getSpecialiseValue()

      if portal.portal_catalog.getResultValue(
        portal_type="Instance Node",
        specialise__uid=software_instance.getUid()
      ) is None:
        instance_node = portal.compute_node_module.newContent(
          portal_type='Instance Node',
          title=instance_tree.getTitle(),
          specialise_value=software_instance,
          follow_up_value=software_instance.getFollowUpValue(),
          activate_kw=activate_kw
        )
        instance_node.validate()
