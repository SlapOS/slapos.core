# TODO
# + review the code
# + put a slash ('/') at the end of the directories' name in MCA


import numpy as np
import re
import json
import os.path

def get_end_and_json_list(start, in_data_stream, max_scan_size = 1024 ** 3):
  """
    Determine the end index of a scan (i.e. the complete scan of a filesystem).
    Return the end index and a list of strings assumed to be valid json strings.
    (This assumes the scanning of the file system produces correct strings.)
  """
  chunk_size = 1024 # * 1024
  while chunk_size < max_scan_size:
    end = min(start+chunk_size, in_data_stream.getSize())
    unpacked, end = in_data_stream.readMsgpackChunkList(start, end)

    raw_data_string = ''.join(map(chr, unpacked))
    end_scan_regexp = re.compile('.*?\[fluentbit_end\]\n', re.DOTALL)
    complete_scan = end_scan_regexp.match(raw_data_string)
    if not complete_scan:
      chunk_size *= 2
      continue
    chunk_size = len(complete_scan.group()) + 1

    line_list = complete_scan.group().splitlines()
    timestamp_json_regexp = re.compile('.*?:(.*?)\[(.*)\]')
    json_string_list = [timestamp_json_regexp.match(line).group(2)
                        for line in line_list
                        if len(timestamp_json_regexp.match(line).groups()) == 2]

    return start + chunk_size, json_string_list

  raise NotImplementedError(
      'Scan too big (<= '
    + str(chunk_size / 1024 ** 2)
    + ' Mo) or no "fluentbit_end" in the Data Stream.')

def get_triplet_list(json_string_list):
  """
    Parse unpacked and return a triplet list: (path, slice1, slice2).
    path is the path of the processed file, slice1 and slice2 are two parts
    of the md5 digest of the processed file. They are stored in "big endian"
    format, i.e. slice1 is the "bigger part".

    NOTE: timestamps are parsed in case they are needed for future improvement
    but they are not used at the moment.
  """
  json_string_list = json_string_list[:-1]
  tmp_data_list = [json.loads(json_string) for json_string in json_string_list]
  data_list = []

  for data in tmp_data_list:
    in_list = False
    if ('path' in data) and exclude_file_list:
      for exclude_file in exclude_file_list:
        if os.path.commonprefix([data['path'], exclude_file]) == exclude_file:
          in_list = True
          break
    if not in_list:
      data_list.append(data)

  return [(data['path'],
           int(data['hash']['md5'][0:8], 16),
           int(data['hash']['md5'][8:16], 16))
          for data in data_list
          if 'path' in data and 'hash' in data and 'md5' in data['hash']]

def get_uid_list(triplet_list, data_stream):
  """
    Fill the mappings and get the list of UIDs.
    The argument @data_stream is only used to access the mappings.
  """
  uid_list = []
  for triplet in triplet_list:
    data_stream.add_path(triplet, 'test')
    triplet_uid = data_stream.get_uid_from_path(triplet, 'test')
    uid_list += [triplet_uid]

  return uid_list

def create_ndarray(uid_list):
  """
    Takes a UIDs list and returns a UIDs ndarray.
    This function exists so that the stages of the data processing are clear and
    so that if further transformations on the data are needed, one can simply
    add them here without reorganizing the code.
  """
  uid_list.append(-1) # used as a delimiter between the scans

  return np.ndarray((len(uid_list),), 'int64', np.array(uid_list))


progress_indicator = in_stream["Progress Indicator"]
in_data_stream = in_stream["Data Stream"]
out_data_array = out_array["Data Array"]
exclude_file_list = []
out_data_array.setPublicationSectionList(in_data_stream.getPublicationSectionList())
if 'file_system_image/reference_image' in in_data_stream.getPublicationSectionList():
  if out_data_array.getValidationState() == 'draft':
    out_data_array.validate()
if not out_data_array.getCausality():
  ingestion_line = in_data_stream.getAggregateRelatedValue(portal_type='Data Ingestion Line')
  resource = ingestion_line.getResource()
  exclude_file_list = ingestion_line.getResourceValue().DataProduct_getExcludeFileList()
  out_data_array.edit(causality=resource)

# DEBUG advice: running the script on the whole Data Stream
# (i.e. restarting from the beginning):
#progress_indicator.setIntOffsetIndex(0)
start = progress_indicator.getIntOffsetIndex()
end = in_data_stream.getSize()
if start >= end:
  return
end, json_string_list = get_end_and_json_list(start, in_data_stream)
triplet_list = get_triplet_list(json_string_list)
uid_list = get_uid_list(triplet_list, in_data_stream)
uid_ndarray = create_ndarray(uid_list)


if start == 0:
  zbigarray = None
else:
  zbigarray = out_data_array.getArray()
# DEBUG advice: reset the Data Array:
# NOTE: currently, the Data Array is reset each time a scan is processed
zbigarray = None
if zbigarray is None:
  zbigarray = out_data_array.initArray(shape=(0,), dtype='int64')

if len(uid_ndarray) > 0:
  zbigarray.append(uid_ndarray)

if end > start:
  progress_indicator.setIntOffsetIndex(end)

# tell caller to create new activity after processing
# if we did not reach end of stream
if end < in_data_stream.getSize():
  return 1
