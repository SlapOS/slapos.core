##############################################################################
#
# Copyright (c) 2002-2021 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################


from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
import json

class testSlapOSAbyss(SlapOSTestCaseMixin):

  def afterSetUp(self):
    super(testSlapOSAbyss, self).afterSetUp()
    self.tic()
    test_organisation = getattr(self.portal.organisation_module, 'test_organisation', None)
    if not test_organisation:
      test_organisation = self.portal.organisation_module.newContent(portal_type='Organisation', id='test_organisation')
    self.compute_node_list = []
    for compute_node_id in ('database_debian10', 'database_debian11', 'node_debian10', 'node_debian11'):
      compute_node =  getattr(self.portal.compute_node_module, compute_node_id, None)
      if compute_node is None:
        compute_node = self.portal.compute_node_module.newContent(
          portal_type='Compute Node',
          id=compute_node_id,
          reference=compute_node_id)
        self.tic()
      data_supply = compute_node.ComputeNode_createDataSupply(batch=1)
      self.compute_node_list.append(compute_node)
      if not data_supply.getDestination():
        data_supply.edit(
          source_value = test_organisation,
          source_section_value = test_organisation,
          destination_value = test_organisation,
          destination_section_value = test_organisation)

      compute_node.ComputeNode_createDataTransformation(batch=1)
    # last one is only used to check data inside data array test
    self.compute_node_list.pop()

    self.portal.compute_node_module['database_debian10'].edit(publication_section_list =['file_system_image/database_image', 'file_system_image/distribution/debian/debian10'])
    self.portal.compute_node_module['database_debian11'].edit(publication_section_list =['file_system_image/database_image', 'file_system_image/distribution/debian/debian11'])
    self.portal.compute_node_module['database_debian11'].edit(exclude_path_list=[])

    self.portal.compute_node_module['node_debian10'].edit(publication_section_list =['file_system_image/node_image', 'file_system_image/distribution/debian/debian10'])
    if not getattr(self.portal.portal_categories.publication_section.file_system_image.distribution, 'test_distribution', None):
      test_distribution = self.portal.portal_categories.publication_section.file_system_image.distribution.newContent(portal_type='Category', id='test_distribution')
      test_distribution.newContent(portal_category='Category', id='debian10', title='debian10', int_index=2)
      test_distribution.newContent(portal_category='Category', id='debian11', title='debian11', int_index=1)

    self.tic()

  def beforeTearDown(self):
    data_stream_id_list = []
    data_ingestion_id_list = []
    data_array_id_list = []
    data_analysis_id_list = []
    for compute_node in self.portal.portal_catalog(portal_type='Compute Node', reference=('database_debian10', 'database_debian11', 'node_debian10', 'node_debian11')):
      data_analysis_line = compute_node.getResourceRelatedValue(portal_type='Data Analysis Line')
      data_ingestion_line = compute_node.getResourceRelatedValue(portal_type='Data Ingestion Line')
      data_array_list = compute_node.getCausalityRelatedValueList(portal_type='Data Array')
      if data_ingestion_line:
        data_stream = data_ingestion_line.getAggregateDataStreamValue()
        data_ingestion_id_list.append(data_ingestion_line.getParentValue().getId())
        if data_stream:
          data_stream_id_list.append(data_stream.getId())

      if data_analysis_line:
        data_analysis_id_list.append(data_analysis_line.getParentValue().getId())
      for data_array in data_array_list:
        data_array_id_list.append(data_array.getId())

    self.portal.data_stream_module.manage_delObjects(ids=data_stream_id_list)
    self.portal.data_ingestion_module.manage_delObjects(ids=data_ingestion_id_list)
    self.portal.data_array_module.manage_delObjects(ids=data_array_id_list)
    self.portal.data_analysis_module.manage_delObjects(ids=data_analysis_id_list)
    self.tic()

  def _create_request_dict(self):
    return {
      'node_debian10': '{"beginning_date": "2022/11/15 17:07 CET"}\n\
{"mac_address": "fe:27:02:3d:26:26"}\n\
{"path": "/sysroot/home/test3/metadata-collect-agent/scan-filesystem/cython/command-line.main.pyx", "stat": {"st_dev": 65025, "st_ino": 150519, "st_mode": 33188, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 9153, "st_blksize": 4096, "st_blocks": 24, "st_atime": 1634293139, "st_mtime": 1632486702, "st_ctime": 1632486702, "st_atime_ns": 958685043, "st_mtime_ns": 839359789, "st_ctime_ns": 839359789}, "hash": {"md5": "8e29c0d260293bc592200a4ef37729e5", "sha1": "fed552c1e74f54275ba4f1106a51a3349e12bbda", "sha256": "776f9da4bc9ba9062c8ab9b8c0a2ab91ad204d6f1e1a7734be050c5d83db2a48", "sha512": "4c547b2c1b0cb76b6e960c21d34e758cd467158f7681042d80d2b7afdde697fdd33fa694e4075a2584bf18caa58a55ec3b15c4b3c13dc59288a216837f4a8d82"}}\n\
{}\n\
{"end_date": "2022/11/15 17:08 CET", "end_marker": "fluentbit_end"}\n',

      'database_debian10': '{"beginning_date": "2022/11/15 17:07 CET"}\n\
{"mac_address": "fe:27:02:3d:26:26"}\n\
{}\n\
{"end_date": "2022/11/15 17:07 CET", "end_marker": "fluentbit_end"}\n',

      'database_debian11': '{"beginning_date": "2022/11/15 17:07 CET"}\n\
{"mac_address": "fe:27:02:3d:26:26"}\n\
{"path": "/home/test3/metadata-collect-agent/scan-filesystem/cython", "stat": {"st_dev": 65025, "st_ino": 150513, "st_mode": 16877, "st_nlink": 6, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 4096, "st_blksize": 4096, "st_blocks": 8, "st_atime": 1634303447, "st_mtime": 1634303457, "st_ctime": 1634303457, "st_atime_ns": 659600793, "st_mtime_ns": 447628573, "st_ctime_ns": 447628573}}\n\
{"path": "/home/test3/metadata-collect-agent/scan-filesystem/cython/command-line.main.pyx", "stat": {"st_dev": 65025, "st_ino": 150519, "st_mode": 33188, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 9153, "st_blksize": 4096, "st_blocks": 24, "st_atime": 1634293139, "st_mtime": 1632486702, "st_ctime": 1632486702, "st_atime_ns": 958685043, "st_mtime_ns": 839359789, "st_ctime_ns": 839359789}, "hash": {"md5": "8e29c0d260293bc592200a4ef37729e5", "sha1": "fed552c1e74f54275ba4f1106a51a3349e12bbda", "sha256": "776f9da4bc9ba9062c8ab9b8c0a2ab91ad204d6f1e1a7734be050c5d83db2a48", "sha512": "4c547b2c1b0cb76b6e960c21d34e758cd467158f7681042d80d2b7afdde697fdd33fa694e4075a2584bf18caa58a55ec3b15c4b3c13dc59288a216837f4a8d82"}}\n\
{"path": "/home/test3/metadata-collect-agent/scan-filesystem/cython/test.main.pyx", "stat": {"st_dev": 65025, "st_ino": 150592, "st_mode": 33188, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 10359, "st_blksize": 4096, "st_blocks": 24, "st_atime": 1634286743, "st_mtime": 1632487276, "st_ctime": 1632487276, "st_atime_ns": 583684050, "st_mtime_ns": 164380968, "st_ctime_ns": 164380968}, "hash": {"md5": "a81f35167d92ba1bcafe643890a68d31", "sha1": "eb300bc4d66fc641237ffe43f990cda05431a73f", "sha256": "bd8a0403f0acf7fce29a8728e1efcbb26f8ca2ee663b12dffcd49ec729be692b", "sha512": "fe19cf16c194adc70bef79945f70904c6d76f12dbd684cb7415885addd923f76f57841c8a68ec350c26ab6abb3f1c7e74a69f4f650c6674702a638c62e29aa4f"}}\n\
{"path": "/home/test3/metadata-collect-agent/scan-filesystem/cython/parse_link_errors.py", "stat": {"st_dev": 65025, "st_ino": 148852, "st_mode": 33261, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 822, "st_blksize": 4096, "st_blocks": 8, "st_atime": 1634301617, "st_mtime": 1634301600, "st_ctime": 1634301600, "st_atime_ns": 70528398, "st_mtime_ns": 658499228, "st_ctime_ns": 658499228}, "hash": {"md5": "465ab32cdc7531623c1130211b30d20c", "sha1": "3439417bacc24c55db7f6b62256122cab5c4cdc7", "sha256": "64214702209370590c7976b599b5a4b1033e175460c9e8a8bb1c133614cd8dac", "sha512": "28b74c2b9e7b93d9e354c35d618cf94cb6285fc62bc1d94ce31fdc5a2d1fc42b8325bcf1292c71351422f66b2d121670b0dbaaffba2107de0ee5d4f19581c64d"}}\n\
{}\n\
{"end_date": "2022/11/15 17:08 CET", "end_marker": "fluentbit_end"}\n'
    }

  def _getRelatedDataStream(self, compute_node):
    return self._getRelatedDataStreamList(compute_node)[0]

  def _getRelatedDataStreamList(self, compute_node):
    data_ingestion_line = compute_node.getResourceRelatedValue(portal_type='Data Ingestion Line')
    if data_ingestion_line:
      return data_ingestion_line.getAggregateValueList(portal_type='Data Stream')

  def _getRelatedDataArrayList(self, compute_node):
    data_array_list = compute_node.getCausalityRelatedValueList(portal_type='Data Array')
    # ascending by creation date
    return sorted(data_array_list, key=lambda x: x.getCreationDate())

  def _ingestData(self, request_dict=None):
    request = self.portal.REQUEST
    if not request_dict:
      request_dict = self._create_request_dict()
    for reference in request_dict:
      request.environ["REQUEST_METHOD"] = 'POST'
      request.set('reference', reference)
      request.set('data_chunk', request_dict[reference])
      request.set('QUERY_STRING', 'ingestion_policy=metadata_upload')
      self.portal.portal_slap.ingestData()
    self.tic()
    return request_dict

  def test_data_ingestion(self):
    request_dict = self._ingestData()
    self.tic()
    for compute_node in self.compute_node_list:
      data_stream = self._getRelatedDataStream(compute_node)
      self.assertEqual(request_dict[compute_node.getReference()], data_stream.getData())

  def test_data_ingestion_create_only_one_data_stream_per_compute_node(self):
    self._ingestData()
    self.tic()
    size_list = []
    for compute_node in self.compute_node_list:
      data_stream_list = self._getRelatedDataStreamList(compute_node)
      self.assertEqual(len(data_stream_list), 1)
      size_list.append(data_stream_list[0].getSize())

    self._ingestData()
    self.tic()
    for i in range(3):
      compute_node = self.compute_node_list[i]
      data_stream_list = self._getRelatedDataStreamList(compute_node)
      self.assertEqual(len(data_stream_list), 1)
      # double size
      self.assertEqual(data_stream_list[0].getSize(),size_list[i]*2)

  def string_to_array(self, reference, string):
    json_string_list = string.splitlines()[:-1]
    data_list = [json.loads(json_string) for json_string in json_string_list]
    if reference == 'node_debian10':
      triplet_list = [("/".join([''] + data['path'].split('/')[2:]), data['hash']['sha256']) for data in data_list if 'path' in data and 'hash' in data and 'sha256' in data['hash']]
    else:
      triplet_list = [(data['path'], data['hash']['sha256']) for data in data_list if 'path' in data and 'hash' in data and 'sha256' in data['hash']]

    data_mapping = self.portal.Base_getDataMapping()
    uid_list = []
    for triplet in triplet_list:
      triplet_uid = data_mapping.addObject(triplet)
      uid_list.append(triplet_uid)

    return uid_list


  def test_data_transformation(self):
    request_dict = self._ingestData()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()

    array_dict = {}
    for reference in request_dict:
      array_dict[reference] = self.string_to_array(reference, request_dict[reference])

    for compute_node in self.compute_node_list:
      data_array_list = self._getRelatedDataArrayList(compute_node)
      self.assertEqual(len(data_array_list),1)
      self.assertEqual(data_array_list[0].getArray()[:].tolist(), array_dict[compute_node.getReference()])
      self.assertEqual(len(data_array_list[0].DataArray_getArrayFileInfoList()), len(array_dict[compute_node.getReference()]))
    # no more data
    for data_analysis in self.portal.portal_catalog(portal_type = "Data Analysis", simulation_state = "started"):
      self.assertEqual(data_analysis.DataAnalysis_executeDataOperation(), None)

  def test_data_transformation_with_exclude_path(self):
    request = self.portal.REQUEST
    request_dict = self._create_request_dict()
    # only test compute node: database_debian11 is enough
    request_dict.pop('node_debian10')
    request_dict.pop('database_debian10')
    self._ingestData(request_dict)
    self.tic()

    database_debian11 = self.portal.compute_node_module['database_debian11']
    data_stream = self._getRelatedDataStream(database_debian11)
    self.assertTrue(data_stream is not None)
    database_debian11.edit(exclude_path_list=['/home/test3/metadata-collect-agent/scan-filesystem/cython/parse_link_errors.py'])
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    data_array = self._getRelatedDataArrayList(database_debian11)[0]
    # /home/test3/metadata-collect-agent/scan-filesystem/cython/command-line.main.pyx, /home/test3/metadata-collect-agent/scan-filesystem/cython/test.main.pyx
    self.assertEqual(len(data_array.getArray()), 2)
    database_debian11.edit(exclude_path_list=['/home/test3/metadata-collect-agent/scan-filesystem/cython'])
    self.tic()
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    request = self.portal.REQUEST
    request.environ["REQUEST_METHOD"] = 'POST'
    request.set('reference', 'database_debian11')
    request.set('data_chunk', request_dict['database_debian11'])
    request.set('QUERY_STRING', 'ingestion_policy=metadata_upload')
    self.portal.portal_slap.ingestData()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    new_array_list = self._getRelatedDataArrayList(database_debian11)
    for new_array in new_array_list:
      if 'file_system_image/process_state/converted' in new_array.getPublicationSectionList():
        break
    self.assertIn('file_system_image/process_state/converted', new_array.getPublicationSectionList())
    self.assertEqual(len(new_array.getArray()), 0)


  def test_data_processing_for_the_first_access(self):
    self._ingestData()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    for compute_node in self.compute_node_list:
      # only one data array is created
      data_array_list = self._getRelatedDataArrayList(compute_node)
      self.assertEqual(len(data_array_list), 1)
      self.assertEqual(data_array_list[0].getPublicationSectionList(), compute_node.getPublicationSectionList() + ['file_system_image/first_access', 'file_system_image/process_state/converted'])

    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    for compute_node in self.compute_node_list:
      # still one data array is created
      data_array_list = self._getRelatedDataArrayList(compute_node)
      self.assertEqual(len(data_array_list), 1)
      self.assertEqual(data_array_list[0].getPublicationSectionList(), compute_node.getPublicationSectionList() + ['file_system_image/first_access', 'file_system_image/process_state/processed'])

  def test_data_processing_no_data_array_is_created_if_previous_isnot_processed(self):
    self._ingestData()
    self.tic()
    # now ingest different data for node_debian10
    request_dict =  {
      'node_debian10': '{"beginning_date": "2022/11/15 17:07 CET"}\n\
{"mac_address": "fe:27:02:3d:26:26"}\n\
{"path": "/sysroot/home/test3/metadata-collect-agent/scan-filesystem/cython/command-line.main.pyx", "stat": {"st_dev": 65025, "st_ino": 150519, "st_mode": 33188, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 9153, "st_blksize": 4096, "st_blocks": 24, "st_atime": 1634293139, "st_mtime": 1632486702, "st_ctime": 1632486702, "st_atime_ns": 958685043, "st_mtime_ns": 839359789, "st_ctime_ns": 839359789}, "hash": {"md5": "8e29c0d260293bc592200a4ef37729e5", "sha1": "fed552c1e74f54275ba4f1106a51a3349e12bbda", "sha256": "VALUE_MODIFIED", "sha512": "4c547b2c1b0cb76b6e960c21d34e758cd467158f7681042d80d2b7afdde697fdd33fa694e4075a2584bf18caa58a55ec3b15c4b3c13dc59288a216837f4a8d82"}}\n\
{}\n\
{"end_date": "2022/11/15 17:08 CET", "end_marker": "fluentbit_end"}\n'
    }
    self._ingestData(request_dict)
    self.tic()
    # ingest data again
    self._ingestData()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()

    # now each compute node should have 1 data arrays
    for compute_node in self.compute_node_list:
      data_array_list = self._getRelatedDataArrayList(compute_node)
      self.assertEqual(len(data_array_list), 1)
      self.assertIn("file_system_image/process_state/converted", data_array_list[0].getPublicationSectionList())

    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()

    # each compute node still should have 1 data arrays, no data array is created because previous one is not finished to process
    for compute_node in self.compute_node_list:
      data_array_list = self._getRelatedDataArrayList(compute_node)
      self.assertEqual(len(data_array_list), 1)
      self.assertIn("file_system_image/process_state/converted", data_array_list[0].getPublicationSectionList())

    # process data array
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    # now each compute node should have 2 data arrays
    for compute_node in self.compute_node_list:
      data_array_list = self._getRelatedDataArrayList(compute_node)
      self.assertEqual(len(data_array_list), 2)
      self.assertIn("file_system_image/process_state/converted", data_array_list[-1].getPublicationSectionList())


    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    # still the same
    for compute_node in self.compute_node_list:
      data_array_list = self._getRelatedDataArrayList(compute_node)
      self.assertEqual(len(data_array_list), 2)
      self.assertIn("file_system_image/process_state/converted", data_array_list[-1].getPublicationSectionList())


    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    # 3 arrays, 2 previous and 1 diff with itself
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 3)
    self.assertTrue(data_array_list[-1].getPredecessorValue() is not None)

    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    # 3 previous, 1 diff with database_debian10
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 4)
    self.assertTrue(data_array_list[-1].getPredecessorValue() is not None)
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    # 4 previous, 1 diff with database_debian11
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertTrue(data_array_list[-1].getPredecessorValue() is not None)
    self.assertEqual(len(data_array_list), 5)

    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    # still the same, previous not finished
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 5)

    # no more database to compare
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 6)
    self.assertTrue(data_array_list[-1].getPredecessorValue() is None)

  def test_data_processing_for_sequence_data_ingestion(self):
    # first access
    self._ingestData()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    # ingest data again
    self._ingestData()
    self.tic()

    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    # now each compute node should have 2 data arrays
    for compute_node in self.compute_node_list:
      data_array_list = self._getRelatedDataArrayList(compute_node)
      self.assertEqual(len(data_array_list), 2)
      self.assertIn("file_system_image/process_state/converted", data_array_list[-1].getPublicationSectionList())


    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['database_debian10'])
    self.assertEqual(len(data_array_list), 2)
    self.assertIn("file_system_image/process_state/archived", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())


    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['database_debian11'])
    self.assertEqual(len(data_array_list), 2)
    self.assertIn("file_system_image/process_state/archived", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())

    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 2)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())

    self.assertIn('file_system_image/diff_end/identical', data_array_list[1].getPublicationSectionList())

    # now ingest different data for node_debian10
    request_dict =  {
      'node_debian10': '{"beginning_date": "2022/11/15 17:07 CET"}\n\
{"mac_address": "fe:27:02:3d:26:26"}\n\
{"path": "/sysroot/home/test3/metadata-collect-agent/scan-filesystem/cython/command-line.main.pyx", "stat": {"st_dev": 65025, "st_ino": 150519, "st_mode": 33188, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 9153, "st_blksize": 4096, "st_blocks": 24, "st_atime": 1634293139, "st_mtime": 1632486702, "st_ctime": 1632486702, "st_atime_ns": 958685043, "st_mtime_ns": 839359789, "st_ctime_ns": 839359789}, "hash": {"md5": "8e29c0d260293bc592200a4ef37729e5", "sha1": "fed552c1e74f54275ba4f1106a51a3349e12bbda", "sha256": "VALUE_MODIFIED", "sha512": "4c547b2c1b0cb76b6e960c21d34e758cd467158f7681042d80d2b7afdde697fdd33fa694e4075a2584bf18caa58a55ec3b15c4b3c13dc59288a216837f4a8d82"}}\n\
{}\n\
{"end_date": "2022/11/15 17:08 CET", "end_marker": "fluentbit_end"}\n'
    }
    self._ingestData(request_dict)
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 3)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())
    # This is the new one with different value
    self.assertIn("file_system_image/process_state/converted", data_array_list[2].getPublicationSectionList())

    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 4)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[2].getPublicationSectionList())
    # array 3 is the result of array 0 and array 2, Note: array 0 is the first access data
    self.assertIn("file_system_image/process_state/converted", data_array_list[3].getPublicationSectionList())

    predecessor_list = [x.getRelativeUrl() for x in data_array_list[3].getPredecessorValueList(portal_type='Data Array')]
    self.assertIn(data_array_list[0].getRelativeUrl(), predecessor_list)
    self.assertIn(data_array_list[2].getRelativeUrl(), predecessor_list)
    # only have one diff
    self.assertTrue(len(data_array_list[3].getArray()), 1)

    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    # array 3 compare with database_debian10
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 5)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[2].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[3].getPublicationSectionList())
    # array 4 is result of array 3 and database_debian10
    self.assertIn("file_system_image/process_state/converted", data_array_list[4].getPublicationSectionList())

    predecessor_list = [x.getRelativeUrl() for x in data_array_list[4].getPredecessorValueList(portal_type='Data Array')]
    last_detabase_debian10 = self._getRelatedDataArrayList(self.portal.compute_node_module['database_debian10'])[-1]
    self.assertIn(last_detabase_debian10.getRelativeUrl(), predecessor_list)
    self.assertIn(data_array_list[3].getRelativeUrl(), predecessor_list)
    self.assertTrue(len(data_array_list[4].getArray()), 1)

    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    # array 4 compare with database_debian11
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 6)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[2].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[3].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[4].getPublicationSectionList())
    # array 5 is result of array 4 and database_debian11
    self.assertIn("file_system_image/process_state/converted", data_array_list[5].getPublicationSectionList())

    predecessor_list = [x.getRelativeUrl() for x in data_array_list[5].getPredecessorValueList(portal_type='Data Array')]
    last_detabase_debian11 = self._getRelatedDataArrayList(self.portal.compute_node_module['database_debian11'])[-1]
    self.assertIn(last_detabase_debian11.getRelativeUrl(), predecessor_list)
    self.assertIn(data_array_list[4].getRelativeUrl(), predecessor_list)
    self.assertTrue(len(data_array_list[5].getArray()), 1)

    # no more database to compare
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    self.assertIn("file_system_image/process_state/processed", data_array_list[5].getPublicationSectionList())
    self.assertIn('file_system_image/diff_end/different', data_array_list[5].getPublicationSectionList())

  def test_data_processing_for_multi_data_ingestion(self):
    # almost same as test_data_processing_for_sequence_data_ingestion
    # except ingest multi data instead of one by one

    # 3 multi data ingestions for node debian10
    # 2 multi data ingestions for database
    self._ingestData()
    self.tic()
    # ingest data again
    self._ingestData()
    self.tic()
    # now ingest different data for node_debian10
    request_dict =  {
      'node_debian10': '{"beginning_date": "2022/11/15 17:07 CET"}\n\
{"mac_address": "fe:27:02:3d:26:26"}\n\
{"path": "/sysroot/home/test3/metadata-collect-agent/scan-filesystem/cython/command-line.main.pyx", "stat": {"st_dev": 65025, "st_ino": 150519, "st_mode": 33188, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 9153, "st_blksize": 4096, "st_blocks": 24, "st_atime": 1634293139, "st_mtime": 1632486702, "st_ctime": 1632486702, "st_atime_ns": 958685043, "st_mtime_ns": 839359789, "st_ctime_ns": 839359789}, "hash": {"md5": "8e29c0d260293bc592200a4ef37729e5", "sha1": "fed552c1e74f54275ba4f1106a51a3349e12bbda", "sha256": "VALUE_MODIFIED", "sha512": "4c547b2c1b0cb76b6e960c21d34e758cd467158f7681042d80d2b7afdde697fdd33fa694e4075a2584bf18caa58a55ec3b15c4b3c13dc59288a216837f4a8d82"}}\n\
{}\n\
{"end_date": "2022/11/15 17:08 CET", "end_marker": "fluentbit_end"}\n'
    }
    self._ingestData(request_dict)
    self.tic()

    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()

    # now each compute node should have 1 data arrays
    for compute_node in self.compute_node_list:
      data_array_list = self._getRelatedDataArrayList(compute_node)
      self.assertEqual(len(data_array_list), 1)
      self.assertIn("file_system_image/process_state/converted", data_array_list[0].getPublicationSectionList())


    # process data array
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['database_debian10'])
    self.assertEqual(len(data_array_list), 1)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())


    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['database_debian11'])
    self.assertEqual(len(data_array_list), 1)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())


    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 1)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())


    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    # now each compute node should have 2 data arrays
    for compute_node in self.compute_node_list:
      data_array_list = self._getRelatedDataArrayList(compute_node)
      self.assertEqual(len(data_array_list), 2)
      self.assertIn("file_system_image/process_state/converted", data_array_list[-1].getPublicationSectionList())


    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['database_debian10'])
    self.assertEqual(len(data_array_list), 2)
    self.assertIn("file_system_image/process_state/archived", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())


    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['database_debian11'])
    self.assertEqual(len(data_array_list), 2)
    self.assertIn("file_system_image/process_state/archived", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())

    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 2)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())
    self.assertIn('file_system_image/diff_end/identical', data_array_list[1].getPublicationSectionList())

    self.portal.ERP5Site_createDataAnalysisList()
    self.portal.ERP5Site_executeDataAnalysisList()
    self.tic()
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 3)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())
    # This is the new one with different value
    self.assertIn("file_system_image/process_state/converted", data_array_list[2].getPublicationSectionList())
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 4)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[2].getPublicationSectionList())
    # array 3 is the result of array 0 and array 2, Note: array 0 is the first access data
    self.assertIn("file_system_image/process_state/converted", data_array_list[3].getPublicationSectionList())
    predecessor_list = [x.getRelativeUrl() for x in data_array_list[3].getPredecessorValueList(portal_type='Data Array')]
    self.assertIn(data_array_list[0].getRelativeUrl(), predecessor_list)
    self.assertIn(data_array_list[2].getRelativeUrl(), predecessor_list)
    # only have one diff
    self.assertTrue(len(data_array_list[3].getArray()), 1)

    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    # array 3 compare with database_debian10
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 5)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[2].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[3].getPublicationSectionList())
    # array 4 is result of array 3 and database_debian10
    self.assertIn("file_system_image/process_state/converted", data_array_list[4].getPublicationSectionList())
    predecessor_list = [x.getRelativeUrl() for x in data_array_list[4].getPredecessorValueList(portal_type='Data Array')]
    last_detabase_debian10 = self._getRelatedDataArrayList(self.portal.compute_node_module['database_debian10'])[-1]
    self.assertIn(last_detabase_debian10.getRelativeUrl(), predecessor_list)
    self.assertIn(data_array_list[3].getRelativeUrl(), predecessor_list)
    self.assertTrue(len(data_array_list[4].getArray()), 1)

    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    # array 4 compare with database_debian11
    data_array_list = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])
    self.assertEqual(len(data_array_list), 6)
    self.assertIn("file_system_image/process_state/processed", data_array_list[0].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[1].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[2].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[3].getPublicationSectionList())
    self.assertIn("file_system_image/process_state/processed", data_array_list[4].getPublicationSectionList())
    # array 5 is result of array 4 and database_debian11
    self.assertIn("file_system_image/process_state/converted", data_array_list[5].getPublicationSectionList())

    predecessor_list = [x.getRelativeUrl() for x in data_array_list[5].getPredecessorValueList(portal_type='Data Array')]
    last_detabase_debian11 = self._getRelatedDataArrayList(self.portal.compute_node_module['database_debian11'])[-1]
    self.assertIn(last_detabase_debian11.getRelativeUrl(), predecessor_list)
    self.assertIn(data_array_list[4].getRelativeUrl(), predecessor_list)
    self.assertTrue(len(data_array_list[5].getArray()), 1)

    # no more database to compare
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    self.assertIn("file_system_image/process_state/processed", data_array_list[5].getPublicationSectionList())
    self.assertIn('file_system_image/diff_end/different', data_array_list[5].getPublicationSectionList())


  def test_data_processing_check_copmute_node_state(self):

    self._ingestData()
    self.tic()
    self._ingestData()
    self.tic()
    # now ingest different data for node_debian10
    request_dict =  {
      'node_debian10': '{"beginning_date": "2022/11/15 17:07 CET"}\n\
{"mac_address": "fe:27:02:3d:26:26"}\n\
{"path": "/sysroot/home/test3/metadata-collect-agent/scan-filesystem/cython/command-line.main.pyx", "stat": {"st_dev": 65025, "st_ino": 150519, "st_mode": 33188, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 9153, "st_blksize": 4096, "st_blocks": 24, "st_atime": 1634293139, "st_mtime": 1632486702, "st_ctime": 1632486702, "st_atime_ns": 958685043, "st_mtime_ns": 839359789, "st_ctime_ns": 839359789}, "hash": {"md5": "8e29c0d260293bc592200a4ef37729e5", "sha1": "fed552c1e74f54275ba4f1106a51a3349e12bbda", "sha256": "VALUE_MODIFIED", "sha512": "4c547b2c1b0cb76b6e960c21d34e758cd467158f7681042d80d2b7afdde697fdd33fa694e4075a2584bf18caa58a55ec3b15c4b3c13dc59288a216837f4a8d82"}}\n\
{}\n\
{"end_date": "2022/11/15 17:08 CET", "end_marker": "fluentbit_end"}\n'
    }
    self._ingestData(request_dict)
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    default_array = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])[-1]
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    self.assertTrue(self.portal.compute_node_module['node_debian10'].ComputeNode_hasModifiedFile() is None)
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    modified_array = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])[-1]
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    last_diff_array = self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])[-1]
    self.assertIn(modified_array.getReference(), last_diff_array.getReference())
    self.assertIn(default_array.getReference(), last_diff_array.getReference())
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    # no more database to compare
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    data_array = self.portal.compute_node_module['node_debian10'].ComputeNode_hasModifiedFile()
    self.assertTrue(data_array is not None)
    data_array.invalidate()
    self.tic()
    self.assertTrue(self.portal.compute_node_module['node_debian10'].ComputeNode_hasModifiedFile() is None)
    modified_array.DataArray_declareAsDefaultData(batch=1)
    self.tic()
    self.assertEqual(modified_array.getValidationState(), 'validated')
    self.assertEqual(default_array.getValidationState(), 'invalidated')
    # still the same
    modified_array.DataArray_declareAsDefaultData(batch=1)
    self.tic()
    self.assertEqual(modified_array.getValidationState(), 'validated')
    self.assertEqual(default_array.getValidationState(), 'invalidated')
    # ingest again, this time as default array is changed, it should has no more difference
    self._ingestData(request_dict)
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    self.assertIn('file_system_image/diff_end/identical', self._getRelatedDataArrayList(self.portal.compute_node_module['node_debian10'])[-1].getPublicationSectionList())
    self.assertTrue(self.portal.compute_node_module['node_debian10'].ComputeNode_hasModifiedFile() is None)



  def test_data_processing_check_value_in_data_array(self):
     # create data array directly instead of tramsforming from data stream
     # so we can easily check the value after each processing
    server_uid_list_list = [
      [7, 9, 10, 11, 15, 17, 18],
      [2, 8, 14, 24],
      [11, 17, 28, 31],
      [2, 8, 14, 24],
      [11, 17, 28, 31]
    ]
    server_publication_list_list = [
      ['file_system_image/node_image', 'file_system_image/distribution/test_distribution/debian11'],
      ['file_system_image/node_image', 'file_system_image/distribution/test_distribution/debian11'],
      ['file_system_image/node_image', 'file_system_image/distribution/test_distribution/debian11'],
      ['file_system_image/node_image', 'file_system_image/distribution/test_distribution/debian10'],
      ['file_system_image/node_image', 'file_system_image/distribution/test_distribution/debian10']
    ]
    server_uid_ndarray_list = []
    for uid_list in server_uid_list_list:
      server_uid_ndarray_list.append(uid_list)

    reference_uid_list_list = [
      [i for i in range(20, 30)],
      [i for i in range(5, 15)]
    ]
    reference_publication_section_list_list = [
      ['file_system_image/database_image', 'file_system_image/distribution/test_distribution/debian11'],
      ['file_system_image/database_image', 'file_system_image/distribution/test_distribution/debian10']
    ]

    reference_uid_ndarray_list = []
    for uid_list in reference_uid_list_list:
      reference_uid_ndarray_list.append(uid_list)

    # create empty first access data
    tmp_data_array = self.portal.data_array_module.newContent(portal_type='Data Array', title='first_access_data')
    tmp_data_array.setCausality('compute_node_module/node_debian10')
    tmp_data_array.initArray(shape=(0,), dtype='int64')
    tmp_data_array.setArray([])
    tmp_data_array.setPublicationSectionList(['file_system_image/distribution/test_distribution/debian10', 'file_system_image/first_access', 'file_system_image/process_state/processed'])
    tmp_data_array.validate()

    tmp_data_array = self.portal.data_array_module.newContent(portal_type='Data Array', title='first_access_data')
    tmp_data_array.setCausality('compute_node_module/node_debian11')
    tmp_data_array.initArray(shape=(0,), dtype='int64')
    tmp_data_array.setArray([])
    tmp_data_array.setPublicationSectionList(['file_system_image/distribution/test_distribution/debian11', 'file_system_image/first_access', 'file_system_image/process_state/processed'])
    tmp_data_array.validate()
    self.tic()

    server_data_array_list = []
    for index, uid_ndarray in enumerate(server_uid_ndarray_list):
      tmp_data_array = self.portal.data_array_module.newContent(portal_type='Data Array', title='%s-%s' % (server_publication_list_list[index][0],server_publication_list_list[index][1]))
      if server_publication_list_list[index][1].endswith('debian10'):
        tmp_data_array.setCausality('compute_node_module/node_debian10')
      else:
        tmp_data_array.setCausality('compute_node_module/node_debian11')
      tmp_data_array.initArray(shape=(len(uid_ndarray),), dtype='int64')
      tmp_data_array.setArray(uid_ndarray)
      tmp_data_array.setPublicationSectionList(server_publication_list_list[index] + ['file_system_image/process_state/converted'])
      tmp_data_array.validate()
      server_data_array_list.append(tmp_data_array)
    self.tic()

    reference_data_array_list = []
    for index, uid_ndarray in enumerate(reference_uid_ndarray_list):
      tmp_data_array = self.getPortalObject().data_array_module.newContent(portal_type='Data Array', title='%s-%s' % (reference_publication_section_list_list[index][0], reference_publication_section_list_list[index][1]))
      # mark it, so it can be deleted later
      tmp_data_array.setCausality('compute_node_module/node_debian10')
      tmp_data_array.initArray(shape=(len(uid_ndarray),), dtype='int64')
      tmp_data_array.setArray(uid_ndarray)
      tmp_data_array.setPublicationSectionList(reference_publication_section_list_list[index] + ['file_system_image/process_state/converted'])
      reference_data_array_list.append(tmp_data_array)
      tmp_data_array.validate()
    self.tic()
     # compare with itself
    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()

    diff_server_data_array_list = []
    for i in server_data_array_list:
      self.assertIn("file_system_image/process_state/processed", i.getPublicationSectionList())
      diff_server_data_array_list.append(i.getPredecessorRelatedValue(portal_type='Data Array'))

    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()

    self.assertIn(diff_server_data_array_list[0].getPredecessorRelatedValue(portal_type='Data Array'), reference_data_array_list[0].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_1 = diff_server_data_array_list[0].getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_1.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertIn("file_system_image/process_state/converted", diff_1.getPublicationSectionList())
    self.assertTrue((diff_1.getArray() == [7, 9, 10, 11, 15, 17, 18]).all())

    self.assertIn(diff_server_data_array_list[1].getPredecessorRelatedValue(portal_type='Data Array'), reference_data_array_list[0].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_2 = diff_server_data_array_list[1].getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_2.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertIn("file_system_image/process_state/converted", diff_2.getPublicationSectionList())
    self.assertTrue((diff_2.getArray() == [2, 8, 14]).all())

    self.assertIn(diff_server_data_array_list[2].getPredecessorRelatedValue(portal_type='Data Array'), reference_data_array_list[0].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_3 = diff_server_data_array_list[2].getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_3.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertIn("file_system_image/process_state/converted", diff_3.getPublicationSectionList())

    self.assertTrue((diff_3.getArray() == [11, 17, 31]).all())

    self.assertIn(diff_server_data_array_list[3].getPredecessorRelatedValue(portal_type='Data Array'), reference_data_array_list[1].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_4 = diff_server_data_array_list[3].getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_4.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertIn("file_system_image/process_state/converted", diff_4.getPublicationSectionList())

    self.assertTrue((diff_4.getArray() == [2, 24]).all())

    self.assertIn(diff_server_data_array_list[4].getPredecessorRelatedValue(portal_type='Data Array'), reference_data_array_list[1].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_5 = diff_server_data_array_list[4].getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_5.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertIn("file_system_image/process_state/converted", diff_5.getPublicationSectionList())

    self.assertTrue((diff_5.getArray() == [17, 28, 31]).all(), diff_5.getRelativeUrl())

    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()



    self.assertIn('file_system_image/diff_end/different', diff_4.getPublicationSectionList())
    self.assertIn('file_system_image/diff_end/different', diff_5.getPublicationSectionList())

    self.assertIn(diff_1.getPredecessorRelatedValue(portal_type='Data Array'), reference_data_array_list[1].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_6 = diff_1.getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_6.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertIn("file_system_image/process_state/converted", diff_6.getPublicationSectionList())
    self.assertTrue((diff_6.getArray() == [15, 17, 18]).all(), diff_6.getRelativeUrl())


    self.assertIn(diff_2.getPredecessorRelatedValue(portal_type='Data Array'), reference_data_array_list[1].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_7 = diff_2.getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_7.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertIn("file_system_image/process_state/converted", diff_7.getPublicationSectionList())
    self.assertTrue((diff_7.getArray() == [2]).all(), diff_7.getRelativeUrl())

    self.assertIn(diff_3.getPredecessorRelatedValue(portal_type='Data Array'), reference_data_array_list[1].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_8 = diff_3.getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_8.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertIn("file_system_image/process_state/converted", diff_8.getPublicationSectionList())

    self.assertTrue((diff_8.getArray() == [17, 31]).all(), diff_8.getRelativeUrl())

    self.portal.portal_alarms.slapos_process_data_array.activeSense()
    self.tic()
    for i in [diff_6, diff_7, diff_8]:
      self.assertIn('file_system_image/diff_end/different', i.getPublicationSectionList())
