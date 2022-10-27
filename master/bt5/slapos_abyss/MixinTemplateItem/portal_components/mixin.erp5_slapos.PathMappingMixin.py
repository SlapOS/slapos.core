from BTrees.LOBTree import LOBTree
from BTrees.OLBTree import OLBTree

class PathMappingMixin:
  def _init_mapping(self):
    self.last_uid_path = "" # no path is empty (nor starts with a space)

    path_uid, uid_path, path_hash64, hash64_path = self._get_mappings()

    if path_uid is None or uid_path is None or path_hash64 is None or hash64_path is None:
      path_uid = OLBTree()
      uid_path = LOBTree()
      path_hash64 = OLBTree()
      hash64_path = LOBTree()

      path_uid[self.last_uid_path] = 0
      uid_path[0] = self.last_uid_path
      path_hash64[self.last_uid_path] = self.hash64(self.last_uid_path)
      hash64_path[self.hash64(self.last_uid_path)] = self.last_uid_path

      self._set_mappings(path_uid, uid_path, path_hash64, hash64_path)

    return path_uid, uid_path, path_hash64, hash64_path

  def reset_mappings(self):
    self._set_mappings(None, None, None, None)

  def _get_mappings(self):
    portal = self.getPortalObject()
    module = portal.data_array_module
    return getattr(module, "__path_uid_mapping", None), getattr(module, "__uid_path_mapping", None),  getattr(module, "__path_hash64_mapping", None), getattr(module, "__hash64_path_mapping", None)

  def _set_mappings(self, path_uid, uid_path, path_hash64, hash64_path):
    portal = self.getPortalObject()
    module = portal.data_array_module
    setattr(module, "__path_uid_mapping", path_uid)
    setattr(module, "__uid_path_mapping", uid_path)
    setattr(module, "__path_hash64_mapping", path_hash64)
    setattr(module, "__hash64_path_mapping", hash64_path)

  def add_path(self, path):
    path_uid, uid_path, path_hash64, hash64_path = self._init_mapping()

    if path in path_uid:
      return

    last_uid = path_uid[self.last_uid_path]
    path_uid[path] = last_uid
    uid_path[last_uid] = path
    path_hash64[path] = self.hash64(path)
    hash64_path[self.hash64(path)] = path

    last_uid = last_uid + 1
    path_uid[self.last_uid_path] = last_uid
    uid_path[last_uid] = self.last_uid_path
    path_hash64[self.last_uid_path] = self.hash64(self.last_uid_path)
    hash64_path[self.hash64(self.last_uid_path)] = self.last_uid_path

  def get_uid_from_path(self, path):
    path_uid, _, _, _ = self._init_mapping()
    if path in path_uid:
      return path_uid[path]
    else:
      return None

  def get_path_from_uid(self, uid):
    _, uid_path, _, _ = self._init_mapping()
    if uid in uid_path:
      return uid_path[uid]
    else:
      return None

  def get_hash64_from_path(self, path):
    _, _, path_hash64, _ = self.init_mapping()
    if path in path_hash64:
      return path_hash64[path]
    else:
      return None

  def get_path_from_hash64(self, hash64):
    _, _, _, hash64_path = self._init_mapping()
    if hash64 in hash64_path:
      return hash64_path[hash64]
    else:
      return None

  def hash64(self, path): # NOT IMPLEMENTED
    # WARNING:
    # computing crc64 would require the use of "libscrc.iso()" but "import libscrc" produces an error
    # so this is used as a temporary replacement, and collision resistance is unknown
    #
    # If this function is modified, call update_hash() to update the two mapping dictionaries using hashes.
    # IndexError: string index out of range # TODO
    #return zlib.adler32(path[0])*2**32 + zlib.crc32(path[0]) # requires "import zlib"
    return -2

  def update_hash(self):
    '''
      Recompute hashes of module.__path_hash64_mapping and module.__hash64_path_mapping
      so that they correspond to the current hash64 function.
    '''
    portal = self.getPortalObject()
    module = portal.data_array_module
    _, _, path_hash64, hash64_path = self._init_mapping()

    new_path_hash64 = OLBTree()
    for path in path_hash64:
      new_path_hash64[path] = self.hash64[path]

    new_hash64_path = LOBTree()
    for _, path in hash64_path.iteritems():
      new_hash64_path[self.hash64(path)] = path

    setattr(module, '__path_hash64_mapping', new_path_hash64)
    setattr(module, '__hash64_path_mapping', new_hash64_path)

