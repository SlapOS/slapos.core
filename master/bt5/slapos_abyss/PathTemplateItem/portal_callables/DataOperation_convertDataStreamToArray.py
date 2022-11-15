import numpy as np
import re
import json
import os.path
from DateTime import DateTime

def getEndAndJsonList(start, in_data_stream, chunk_size = 4 * 1024 * 1024):

  end = min(start + chunk_size, in_data_stream.getSize())
  unpacked = in_data_stream.readChunkList(start, end)
  unpacked_string = "".join(unpacked)

  if end < in_data_stream.getSize():
    raw_data_string = '\n'.join(unpacked_string.splitlines()[:-1])
    end = start + len(raw_data_string) + 1
  else:
    raw_data_string = unpacked_string

  end_scan_regexp = re.compile('.*?fluentbit_end"}', re.DOTALL)
  scan_end = end_scan_regexp.match(raw_data_string)
  if not scan_end:
    is_end_of_scan = False
  else:
    is_end_of_scan = True
    end = start + len(scan_end.group()) + 1
    raw_data_string = raw_data_string[:len(scan_end.group())]

  return end, raw_data_string.splitlines(), is_end_of_scan

def getTripletList(json_string_list, is_end_of_scan):
  if is_end_of_scan:
    # this lign deletes the "fluentbit_end" at the end of a scan
    json_string_list = json_string_list[:-1]
  tmp_data_list = []
  for json_string in json_string_list:
    tmp_data_list.append(json.loads(json_string))
  data_list = []
  for data in tmp_data_list:
    in_list = False
    if ('path' in data) and exclude_path_list:
      for exclude_path in exclude_path_list:
        if os.path.commonprefix([data['path'], exclude_path]) == exclude_path:
          in_list = True
          break
    if not in_list:
      data_list.append(data)
  return [(data['path'], data['hash']['sha256']) for data in data_list if 'path' in data and 'hash' in data and 'sha256' in data['hash']]


def getUidList(triplet_list, data_stream):
  uid_list = []
  for triplet in triplet_list:
    triplet_uid = data_mapping.addObject(triplet)
    uid_list.append(triplet_uid)
  return uid_list

progress_indicator = in_stream["Progress Indicator"]
in_data_stream = in_stream["Data Stream"]
data_mapping = in_stream["Data Mapping"]
out_data_array = out_array["Data Array"]
if out_data_array.getSimulationState() == 'converted':
  return

if out_data_array.getSimulationState() == 'draft':
  out_data_array.transformFile()

exclude_path_list = []

if not out_data_array.getCausality():
  ingestion_line = in_data_stream.getAggregateRelatedValue(portal_type='Data Ingestion Line')
  resource_value = ingestion_line.getResourceValue()
  exclude_path_list = ingestion_line.getResourceValue().getProperty('exclude_path_list', [])
  out_data_array.edit(causality_value=resource_value)
  in_data_stream.setPublicationSectionList(resource_value.getPublicationSectionList())
  out_data_array.setPublicationSectionList(resource_value.getPublicationSectionList())


start = progress_indicator.getIntOffsetIndex()
end = in_data_stream.getSize()
if start >= end:
  out_data_array.convertFile()
  return
end, json_string_list, is_end_of_scan = getEndAndJsonList(start, in_data_stream)
if is_end_of_scan:
  stop_date = json.loads(json_string_list[-1])["end_date"]
  out_data_array.edit(stop_date= DateTime(stop_date))
if start == 0:
  start_date = json.loads(json_string_list[0])["beginning_date"]
  out_data_array.edit(start_date = DateTime(start_date))

triplet_list = getTripletList(json_string_list, is_end_of_scan)
uid_list = getUidList(triplet_list, in_data_stream)
uid_ndarray = np.ndarray((len(uid_list),), 'int64', np.array(uid_list))


zbigarray = out_data_array.getArray()

if zbigarray is None:
  zbigarray = out_data_array.initArray(shape=(0,), dtype='int64')

if len(uid_ndarray) > 0:
  zbigarray.append(uid_ndarray)

progress_indicator.setIntOffsetIndex(end)

if is_end_of_scan:
  out_data_array.convertFile()
  return

if end < in_data_stream.getSize():
  return 1

out_data_array.convertFile()
