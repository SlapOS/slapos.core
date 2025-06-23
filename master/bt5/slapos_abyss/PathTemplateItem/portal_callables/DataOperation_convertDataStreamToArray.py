import numpy as np
import re
import json
import os.path
from DateTime import DateTime
from Products.ERP5Type.Utils import bytes2str

def getEndAndJsonList(start, in_data_stream, chunk_size = 4 * 1024 * 1024):

  end = min(start + chunk_size, in_data_stream.getSize())
  unpacked = in_data_stream.readChunkList(start, end)
  unpacked_string = "".join([bytes2str(i) for i in unpacked])

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

def removeFirstPath(data):
  data['path'] = "/".join([''] + data['path'].split('/')[2:])
  return data

def getTripletList(json_string_list, is_end_of_scan):
  if is_end_of_scan:
    # this lign deletes the "fluentbit_end" at the end of a scan
    json_string_list = json_string_list[:-1]
  tmp_data_list = []
  for json_string in json_string_list:
    tmp_data_list.append(json.loads(json_string))

  tmp_data_list = [x for x in tmp_data_list if 'path' in x and 'hash' in x and 'sha256' in x['hash']]
  # when server start with uefi, it is mounted at sysroot which makes path starts with /sysroot instead of /
  if tmp_data_list and tmp_data_list[0]['path'].startswith('/sysroot'):
    tmp_data_list = [removeFirstPath(x) for x in tmp_data_list]

  data_list = []
  for data in tmp_data_list:
    in_list = False
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
publication_section_list = out_data_array.getPublicationSectionList()
if "file_system_image/process_state/converted" in publication_section_list:
  return

ingestion_line = in_data_stream.getAggregateRelatedValue(portal_type='Data Ingestion Line')
exclude_path_list = ingestion_line.getResourceValue().getProperty('exclude_path_list', [])


start = progress_indicator.getIntOffsetIndex()
end = in_data_stream.getSize()
if start >= end:
  out_data_array.convertFile()
  return
end, json_string_list, is_end_of_scan = getEndAndJsonList(start, in_data_stream)
if is_end_of_scan:
  stop_date = json.loads(json_string_list[-1])["end_date"]
  out_data_array.edit(stop_date= DateTime(stop_date))


triplet_list = getTripletList(json_string_list, is_end_of_scan)
uid_list = getUidList(triplet_list, in_data_stream)
uid_ndarray = np.ndarray((len(uid_list),), 'int64', np.array(uid_list))


zbigarray = out_data_array.getArray()

if zbigarray is None:
  zbigarray = out_data_array.initArray(shape=(0,), dtype='int64')
  start_date = json.loads(json_string_list[0])["beginning_date"]
  out_data_array.edit(start_date = DateTime(start_date))

if len(uid_ndarray) > 0:
  zbigarray.append(uid_ndarray)

progress_indicator.setIntOffsetIndex(end)

if is_end_of_scan:
  out_data_array.setPublicationSectionList(publication_section_list + ["file_system_image/process_state/converted"])
  if context.portal_workflow.isTransitionPossible(out_data_array, 'validate'):
    out_data_array.validate()
  return

if end < in_data_stream.getSize():
  return 1
