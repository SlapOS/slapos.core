"""
  Make a list with delta CO2 values
"""

if simulated_cpu_load is not None:
  partition_average_cpu_load = simulated_cpu_load
else:
  partition_average_cpu_load = context.getCpuCapacityQuantity()

partition_delta_co2_dict = {} 

for compute_partition in compute_partition_list:
  compute_node = compute_partition.getParentValue()
  compute_node_zero_emission_ratio = compute_node.ComputeNode_getZeroEmissionRatio()
  compute_node_cpu_load_percentage = compute_node.ComputeNode_getLatestCPUPercentLoad()
  compute_node_watt = compute_node.ComputeNode_getWattConsumption(compute_node_cpu_load_percentage)

  partition_watt = compute_node.ComputeNode_getWattConsumption(
                compute_node_cpu_load_percentage + partition_average_cpu_load)

  delta_watt = (partition_watt-compute_node_watt)

  delta_co2 = delta_watt - delta_watt*(compute_node_zero_emission_ratio/100)

  if delta_co2 in partition_delta_co2_dict:
    partition_delta_co2_dict[delta_co2].append(compute_partition)
  else:
    partition_delta_co2_dict[delta_co2] = [compute_partition]

return partition_delta_co2_dict
