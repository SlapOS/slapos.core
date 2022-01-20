import numpy as np
import re
import json
import os.path

def get_end_and_json_list(start, in_data_stream, chunk_size = 4 * 1024 * 1024):
  """
    Determine the end index of a scan (i.e. the complete scan of a filesystem).
    Return the end index and a list of strings assumed to be valid json strings.
    (This assumes the scanning of the file system produces correct strings.)
  """
  # assume max path size is 4096 and add 4096 for the rest
  max_remaining_for_eol = 8192
  end = min(start + chunk_size + max_remaining_for_eol, in_data_stream.getSize())
  #unpacked, get_end = in_data_stream.readMsgpackChunkList(start, end) # LEGACY
  unpacked = in_data_stream.readChunkList(start, end) # CURRENT
  unpacked_string = "".join(unpacked) # CURRENT

  # extending the current chunk until the next end of line,
  # so json remains valid
  if end < in_data_stream.getSize():
    new_end_index = chunk_size
    while unpacked_string[new_end_index] != '\n': # CURRENT
    #while unpacked[new_end_index] != ord('\n'): # LEGACY
      new_end_index += 1
    end = start + new_end_index + 1

  """ not useful anymore? # LEGACY / TOCLEAN
  unpacked = unpacked[:end]
  try: # efficient but does not prevent errors
    raw_data_string = ''.join(map(chr, unpacked))
  except: # not efficient but does prevent value errors and type errors
    cleaned_unpacked = []
    for i in unpacked:
      if (type(i) == type(1) # only ints
          and 0 <= i and i < 256): # i in range(256)
        cleaned_unpacked.append(i)
    raw_data_string = ''.join(map(chr, cleaned_unpacked))
  #"""
  raw_data_string = unpacked_string[:end] # CURRENT
  end_scan_regexp = re.compile('.*?\[fluentbit_end\]\n', re.DOTALL)
  scan_end = end_scan_regexp.match(raw_data_string)
  if not scan_end:
    is_end_of_scan = False
  else:
    is_end_of_scan = True
    end = start + len(scan_end.group()) + 1
    raw_data_string = raw_data_string[:len(scan_end.group())]

  context.log("DEBUG 020: len(raw_data_string) =", len(raw_data_string))
  context.log("DEBUG 020: type(raw_data_string) =", type(raw_data_string))
  context.log("DEBUG 020: type(raw_data_string[0]) =", type(raw_data_string[0]))
  line_list = raw_data_string.splitlines()
  context.log("DEBUG 020: len(line_list) =", len(line_list))

  timestamp_json_regexp = re.compile(r'.*?:(.*?)\[(.*)\]')
  json_string_list = [timestamp_json_regexp.match(line).group(2)
                      for line in line_list
                      if (timestamp_json_regexp.match(line) and (len(timestamp_json_regexp.match(line).groups()) == 2))]

  return end, json_string_list, is_end_of_scan


def get_triplet_list(json_string_list, is_end_of_scan):
  """
    Parse unpacked and return a triplet list: (path, slice1, slice2).
    path is the path of the processed file, slice1 and slice2 are two parts
    of the md5 digest of the processed file. They are stored in "big endian"
    format, i.e. slice1 is the "bigger part".

    NOTE: timestamps are parsed in case they are needed for future improvement
    but they are not used at the moment.
  """
  if is_end_of_scan:
    # this lign deletes the "fluentbit_end" at the end of a scan
    # because it is not valid json
    json_string_list = json_string_list[:-1]
  tmp_data_list = []
  fail_counter = 0
  for json_string in json_string_list:
    tmp_data_list.append(json.loads(json_string))
    """ CURRENT
    try:
      tmp_data_list.append(json.loads(json_string))
    except:
      context.log('FAILING json_string:', json_string) # DEBUG
      fail_counter += 1
      pass
  if fail_counter > 0:
    context.log('FAILED json_string:', fail_counter) # DEBUG
    #"""

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
  ressource = ingestion_line.getRessource()
  exclude_file_list = ingestion_line.getRessourceValue().DataProduct_getExcludeFileList()
  out_data_array.edit(causality=ressource)

start = progress_indicator.getIntOffsetIndex()
end = in_data_stream.getSize()
if start >= end:
  return
end, json_string_list, is_end_of_scan = get_end_and_json_list(start, in_data_stream)
context.log("DEBUG 020: len(json_string_list) =", len(json_string_list))
triplet_list = get_triplet_list(json_string_list, is_end_of_scan)
context.log("DEBUG 020: len(triplet_list) =", len(triplet_list))
uid_list = get_uid_list(triplet_list, in_data_stream)
context.log("DEBUG 020: len(uid_list) =", len(uid_list))
uid_ndarray = create_ndarray(uid_list)

context.log("len(uid_ndarray) =", len(uid_ndarray))
context.log("start =", start)
context.log("end =", end)

if start == 0:
  zbigarray = None
else:
  zbigarray = out_data_array.getArray()
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
