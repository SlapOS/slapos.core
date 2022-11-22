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
import numpy as np
import json

class testSlapOSAbyss(SlapOSTestCaseMixin):

  def afterSetUp(self):
    super(testSlapOSAbyss, self).afterSetUp()
    self.tic()
    data_product =  getattr(self.portal.data_product_module, 'test_create_action', None)
    if not data_product:
      data_product = self.portal.data_product_module.newContent(
        portal_type='Data Product',
        reference='test_create_action',
        id = 'test_create_action',
        aggregated_portal_type_list = ['Data Stream', 'Progress Indicator']
      )
    self.data_product = data_product
    if not getattr(self.portal.portal_categories.publication_section.file_system_image.distribution, 'test_distribution', None):
      test_distribution = self.portal.portal_categories.publication_section.file_system_image.distribution.newContent(portal_type='Category', id='test_distribution')
      test_distribution.newContent(portal_category='Category', id='debian10', title='debian10', int_index=2)
      test_distribution.newContent(portal_category='Category', id='debian11', title='debian11', int_index=1)

    self.portal.data_product_module['test_server_reference_2'].edit(exclude_path_list=[])
    self.tic()

  def beforeTearDown(self):
    data_stream_id_list = []
    data_ingestion_id_list = []
    data_array_id_list = []
    data_analysis_id_list = []
    for data_product in self.portal.portal_catalog(portal_type='Data Product', reference=('test_server_reference_2', 'test_server', 'test_server_reference_1', 'test_create_action')):
      data_analysis_line = data_product.getResourceRelatedValue(portal_type='Data Analysis Line')
      data_ingestion_line = data_product.getResourceRelatedValue(portal_type='Data Ingestion Line')
      data_array_list = data_product.getCausalityRelatedValueList(portal_type='Data Array')
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
    request_dict = {
      'test_server': '{"beginning_date": "2022/11/15 17:07 CET"}\n\
{"mac_address": "fe:27:02:3d:26:26"}\n\
{"path": "/sysroot/home/test3/metadata-collect-agent/scan-filesystem/cython/command-line.main.pyx", "stat": {"st_dev": 65025, "st_ino": 150519, "st_mode": 33188, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 9153, "st_blksize": 4096, "st_blocks": 24, "st_atime": 1634293139, "st_mtime": 1632486702, "st_ctime": 1632486702, "st_atime_ns": 958685043, "st_mtime_ns": 839359789, "st_ctime_ns": 839359789}, "hash": {"md5": "8e29c0d260293bc592200a4ef37729e5", "sha1": "fed552c1e74f54275ba4f1106a51a3349e12bbda", "sha256": "776f9da4bc9ba9062c8ab9b8c0a2ab91ad204d6f1e1a7734be050c5d83db2a48", "sha512": "4c547b2c1b0cb76b6e960c21d34e758cd467158f7681042d80d2b7afdde697fdd33fa694e4075a2584bf18caa58a55ec3b15c4b3c13dc59288a216837f4a8d82"}}\n\
{}\n\
{"end_date": "2022/11/15 17:08 CET", "end_marker": "fluentbit_end"}\n',

      'test_server_reference_1': '{"beginning_date": "2022/11/15 17:07 CET"}\n\
{"mac_address": "fe:27:02:3d:26:26"}\n\
{}\n\
{"end_date": "2022/11/15 17:07 CET", "end_marker": "fluentbit_end"}\n',

      'test_server_reference_2': '{"beginning_date": "2022/11/15 17:07 CET"}\n\
{"mac_address": "fe:27:02:3d:26:26"}\n\
{"path": "/home/test3/metadata-collect-agent/scan-filesystem/cython", "stat": {"st_dev": 65025, "st_ino": 150513, "st_mode": 16877, "st_nlink": 6, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 4096, "st_blksize": 4096, "st_blocks": 8, "st_atime": 1634303447, "st_mtime": 1634303457, "st_ctime": 1634303457, "st_atime_ns": 659600793, "st_mtime_ns": 447628573, "st_ctime_ns": 447628573}}\n\
{"path": "/home/test3/metadata-collect-agent/scan-filesystem/cython/command-line.main.pyx", "stat": {"st_dev": 65025, "st_ino": 150519, "st_mode": 33188, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 9153, "st_blksize": 4096, "st_blocks": 24, "st_atime": 1634293139, "st_mtime": 1632486702, "st_ctime": 1632486702, "st_atime_ns": 958685043, "st_mtime_ns": 839359789, "st_ctime_ns": 839359789}, "hash": {"md5": "8e29c0d260293bc592200a4ef37729e5", "sha1": "fed552c1e74f54275ba4f1106a51a3349e12bbda", "sha256": "776f9da4bc9ba9062c8ab9b8c0a2ab91ad204d6f1e1a7734be050c5d83db2a48", "sha512": "4c547b2c1b0cb76b6e960c21d34e758cd467158f7681042d80d2b7afdde697fdd33fa694e4075a2584bf18caa58a55ec3b15c4b3c13dc59288a216837f4a8d82"}}\n\
{"path": "/home/test3/metadata-collect-agent/scan-filesystem/cython/test.main.pyx", "stat": {"st_dev": 65025, "st_ino": 150592, "st_mode": 33188, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 10359, "st_blksize": 4096, "st_blocks": 24, "st_atime": 1634286743, "st_mtime": 1632487276, "st_ctime": 1632487276, "st_atime_ns": 583684050, "st_mtime_ns": 164380968, "st_ctime_ns": 164380968}, "hash": {"md5": "a81f35167d92ba1bcafe643890a68d31", "sha1": "eb300bc4d66fc641237ffe43f990cda05431a73f", "sha256": "bd8a0403f0acf7fce29a8728e1efcbb26f8ca2ee663b12dffcd49ec729be692b", "sha512": "fe19cf16c194adc70bef79945f70904c6d76f12dbd684cb7415885addd923f76f57841c8a68ec350c26ab6abb3f1c7e74a69f4f650c6674702a638c62e29aa4f"}}\n\
{"path": "/home/test3/metadata-collect-agent/scan-filesystem/cython/parse_link_errors.py", "stat": {"st_dev": 65025, "st_ino": 148852, "st_mode": 33261, "st_nlink": 1, "st_uid": 1000, "st_gid": 1000, "st_rdev": 0, "st_size": 822, "st_blksize": 4096, "st_blocks": 8, "st_atime": 1634301617, "st_mtime": 1634301600, "st_ctime": 1634301600, "st_atime_ns": 70528398, "st_mtime_ns": 658499228, "st_ctime_ns": 658499228}, "hash": {"md5": "465ab32cdc7531623c1130211b30d20c", "sha1": "3439417bacc24c55db7f6b62256122cab5c4cdc7", "sha256": "64214702209370590c7976b599b5a4b1033e175460c9e8a8bb1c133614cd8dac", "sha512": "28b74c2b9e7b93d9e354c35d618cf94cb6285fc62bc1d94ce31fdc5a2d1fc42b8325bcf1292c71351422f66b2d121670b0dbaaffba2107de0ee5d4f19581c64d"}}\n\
{}\n\
{"end_date": "2022/11/15 17:08 CET", "end_marker": "fluentbit_end"}\n'
    }

    return request_dict

  def test_data_stream_ingestion(self, request_dict=None):
    request = self.portal.REQUEST
    if not request_dict:
      request_dict = self._create_request_dict()
    for reference in request_dict:
      request.environ["REQUEST_METHOD"] = 'POST'
      request.set('reference', reference)
      request.set('data_chunk', request_dict[reference])
      self.portal.portal_ingestion_policies.metadata_upload.ingest()
    self.tic()

    for reference in request_dict:
      data_stream = self.portal.portal_catalog.getResultValue(
        portal_type = 'Data Stream',
        reference = '%s-%s' % (reference, reference)
      )
      self.assertEqual(request_dict[reference], data_stream.getData())

  def string_to_ndarray(self, reference, string):
    json_string_list = string.splitlines()[:-1]
    data_list = [json.loads(json_string) for json_string in json_string_list]
    if reference == 'test_server':
      triplet_list = [("/".join([''] + data['path'].split('/')[2:]), data['hash']['sha256']) for data in data_list if 'path' in data and 'hash' in data and 'sha256' in data['hash']]
    else:
      triplet_list = [(data['path'], data['hash']['sha256']) for data in data_list if 'path' in data and 'hash' in data and 'sha256' in data['hash']]


    data_mapping = self.portal.Base_getDataMapping()
    uid_list = []
    for triplet in triplet_list:
      triplet_uid = data_mapping.addObject(triplet)
      uid_list.append(triplet_uid)

    return np.ndarray((len(uid_list),), 'int64', np.array(uid_list))

  def string_dict_to_ndarray_dict(self, string_dict):
    ndarray_dict = dict()
    for reference in string_dict:
      ndarray_dict[reference] = self.string_to_ndarray(reference, string_dict[reference])

    return ndarray_dict

  def test_data_transformation(self):

    request_dict = self._create_request_dict()
    self.test_data_stream_ingestion(request_dict)

    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()

    control_array_dict = self.string_dict_to_ndarray_dict(request_dict)

    data_array_list = self.portal.portal_catalog(
      portal_type='Data Array'
    )

    ### COMPARE THE DATA ARRAYS
    for data_array in data_array_list:
      dr = data_array.getReference().split('-')[1]
      current_control_array = control_array_dict[dr]

      assert np.array_equal(current_control_array, data_array.array[:])


  def test_data_transformation_with_exclude_path(self):
    request = self.portal.REQUEST
    request_dict = self._create_request_dict()
    request_dict.pop('test_server')
    request_dict.pop('test_server_reference_1')

    request.environ["REQUEST_METHOD"] = 'POST'
    request.set('reference', 'test_server_reference_2')
    request.set('data_chunk', request_dict['test_server_reference_2'])
    self.portal.portal_ingestion_policies.metadata_upload.ingest()
    self.tic()


    data_stream_list = self.portal.portal_catalog(portal_type = 'Data Stream')
    self.assertEqual(len(data_stream_list), 1)
    test_server_reference_2 = self.portal.data_product_module['test_server_reference_2']
    test_server_reference_2.edit(exclude_path_list=['/home/test3/metadata-collect-agent/scan-filesystem/cython/parse_link_errors.py'])
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    data_array = test_server_reference_2.getCausalityRelatedValue(portal_type='Data Array')
    # /home/test3/metadata-collect-agent/scan-filesystem/cython/command-line.main.pyx, /home/test3/metadata-collect-agent/scan-filesystem/cython/test.main.pyx
    self.assertEquals(len(data_array.getArray()), 2)
    test_server_reference_2.edit(exclude_path_list=['/home/test3/metadata-collect-agent/scan-filesystem/cython'])
    self.tic()
    data_array.processFile()
    self.tic()
    request = self.portal.REQUEST
    request.environ["REQUEST_METHOD"] = 'POST'
    request.set('reference', 'test_server_reference_2')
    request.set('data_chunk', request_dict['test_server_reference_2'])
    self.portal.portal_ingestion_policies.metadata_upload.ingest()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    for new_array in test_server_reference_2.getCausalityRelatedValueList(portal_type='Data Array'):
      if new_array.getSimulationState() == 'converted':
        break
    self.assertEquals(new_array.getSimulationState(), 'converted')
    self.assertEquals(len(new_array.getArray()), 0)

  def test_compare_data_array(self):
    ## CREATE DATA TO BE TESTED
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
      server_uid_ndarray_list.append(np.array(uid_list))

    reference_uid_list_list = [
      [i for i in range(20, 30)],
      [i for i in range(5, 15)]
    ]
    reference_publication_section_list_list = [
      ['file_system_image/reference_image', 'file_system_image/distribution/test_distribution/debian11'],
      ['file_system_image/reference_image', 'file_system_image/distribution/test_distribution/debian10']
    ]

    reference_uid_ndarray_list = []
    for uid_list in reference_uid_list_list:
      reference_uid_ndarray_list.append(np.array(uid_list))

    ## Create Data Arrays
    # Node servers
    server_data_array_list = []
    for index, uid_ndarray in enumerate(server_uid_ndarray_list):
      tmp_data_array = self.getPortalObject().data_array_module.newContent(portal_type='Data Array', title='%s-%s' % (server_publication_list_list[index][0],server_publication_list_list[index][1]))
      # mark it, so it can be deleted later
      tmp_data_array.setCausality('data_product_module/test_server')
      tmp_data_array.initArray(shape=(uid_ndarray.size,), dtype='int64')
      tmp_data_array.setArray(uid_ndarray)
      tmp_data_array.setPublicationSectionList(server_publication_list_list[index])
      server_data_array_list.append(tmp_data_array)
      tmp_data_array.convertFile()
    self.tic()

    reference_data_array_list = []
    for index, uid_ndarray in enumerate(reference_uid_ndarray_list):
      tmp_data_array = self.getPortalObject().data_array_module.newContent(portal_type='Data Array', title='%s-%s' % (reference_publication_section_list_list[index][0], reference_publication_section_list_list[index][1]))
      # mark it, so it can be deleted later
      tmp_data_array.setCausality('data_product_module/test_server')
      tmp_data_array.initArray(shape=(uid_ndarray.size,), dtype='int64')
      tmp_data_array.setArray(uid_ndarray)
      tmp_data_array.setPublicationSectionList(reference_publication_section_list_list[index])
      reference_data_array_list.append(tmp_data_array)
      tmp_data_array.convertFile()
    self.tic()

    ## Call DataArray_generateDiff
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()

    for i in server_data_array_list:
      self.assertEqual(i.getSimulationState(), 'processed')


    self.assertTrue(server_data_array_list[0].getPredecessorRelatedValue(portal_type='Data Array') in reference_data_array_list[0].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_1 = server_data_array_list[0].getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_1.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertEqual(diff_1.getSimulationState(), 'converted')
    self.assertTrue((diff_1.getArray() == [7, 9, 10, 11, 15, 17, 18]).all())

    self.assertTrue(server_data_array_list[1].getPredecessorRelatedValue(portal_type='Data Array') in reference_data_array_list[0].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_2 = server_data_array_list[1].getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_2.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertEqual(diff_2.getSimulationState(), 'converted')
    self.assertTrue((diff_2.getArray() == [2, 8, 14]).all())

    self.assertTrue(server_data_array_list[2].getPredecessorRelatedValue(portal_type='Data Array') in reference_data_array_list[0].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_3 = server_data_array_list[2].getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_3.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertEqual(diff_3.getSimulationState(), 'converted')
    self.assertTrue((diff_3.getArray() == [11, 17, 31]).all())

    self.assertTrue(server_data_array_list[3].getPredecessorRelatedValue(portal_type='Data Array') in reference_data_array_list[1].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_4 = server_data_array_list[3].getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_4.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertEqual(diff_4.getSimulationState(), 'converted')
    self.assertTrue((diff_4.getArray() == [2, 24]).all())

    self.assertTrue(server_data_array_list[4].getPredecessorRelatedValue(portal_type='Data Array') in reference_data_array_list[1].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_5 = server_data_array_list[4].getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_5.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertEqual(diff_5.getSimulationState(), 'converted')
    self.assertTrue((diff_5.getArray() == [17, 28, 31]).all(), diff_5.getRelativeUrl())

    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()



    self.assertTrue('file_system_image/diff_end' in diff_4.getPublicationSectionList())
    self.assertTrue('file_system_image/diff_end' in diff_5.getPublicationSectionList())

    self.assertTrue(diff_1.getPredecessorRelatedValue(portal_type='Data Array') in reference_data_array_list[1].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_6 = diff_1.getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_6.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertEqual(diff_6.getSimulationState(), 'converted')
    self.assertTrue((diff_6.getArray() == [15, 17, 18]).all(), diff_6.getRelativeUrl())


    self.assertTrue(diff_2.getPredecessorRelatedValue(portal_type='Data Array') in reference_data_array_list[1].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_7 = diff_2.getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_7.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertEqual(diff_7.getSimulationState(), 'converted')
    self.assertTrue((diff_7.getArray() == [2]).all(), diff_7.getRelativeUrl())

    self.assertTrue(diff_3.getPredecessorRelatedValue(portal_type='Data Array') in reference_data_array_list[1].getPredecessorRelatedValueList(portal_type='Data Array'))
    diff_8 = diff_3.getPredecessorRelatedValue(portal_type='Data Array')
    self.assertEqual(len(diff_8.getPredecessorValueList(portal_type='Data Array')), 2)
    self.assertEqual(diff_8.getSimulationState(), 'converted')
    self.assertTrue((diff_8.getArray() == [17, 31]).all(), diff_8.getRelativeUrl())

    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    for i in [diff_6, diff_7, diff_8]:
      self.assertTrue('file_system_image/diff_end' in i.getPublicationSectionList())


  def test_compare_data_array_change_data_product_state(self):
    test_server = self.portal.data_product_module['test_server']
    if self.portal.portal_workflow.isTransitionPossible(test_server, 'validate'):
      test_server.validate()
    self.assertEquals(test_server.getValidationState(), 'validated')

    server_publication_list = ['file_system_image/node_image', 'file_system_image/distribution/test_distribution/debian11']
    server_uid_ndarray = np.array([7, 9, 10, 11, 15, 17, 18])

    reference_uid_list_list = [
      [i for i in range(20, 30)],
      [i for i in range(5, 15)]
    ]
    reference_publication_section_list_list = [
      ['file_system_image/reference_image', 'file_system_image/distribution/test_distribution/debian11'],
      ['file_system_image/reference_image', 'file_system_image/distribution/test_distribution/debian10']
    ]

    reference_uid_ndarray_list = []
    for uid_list in reference_uid_list_list:
      reference_uid_ndarray_list.append(np.array(uid_list))

    ## Create Data Arrays
    # Node servers
    tmp_data_array = self.getPortalObject().data_array_module.newContent(portal_type='Data Array', title='%s-%s' % (server_publication_list[0],server_publication_list[1]))
    tmp_data_array.setCausality('data_product_module/test_server')
    tmp_data_array.initArray(shape=(server_uid_ndarray.size,), dtype='int64')
    tmp_data_array.setArray(server_uid_ndarray)
    tmp_data_array.setPublicationSectionList(server_publication_list)
    tmp_data_array.convertFile()

    reference_data_array_list = []
    for index, uid_ndarray in enumerate(reference_uid_ndarray_list):
      tmp_data_array = self.getPortalObject().data_array_module.newContent(portal_type='Data Array', title='%s-%s' % (reference_publication_section_list_list[index][0], reference_publication_section_list_list[index][1]))
      tmp_data_array.setCausality('data_product_module/test_server_reference_1')
      tmp_data_array.initArray(shape=(uid_ndarray.size,), dtype='int64')
      tmp_data_array.setArray(uid_ndarray)
      tmp_data_array.setPublicationSectionList(reference_publication_section_list_list[index])
      reference_data_array_list.append(tmp_data_array)
      tmp_data_array.convertFile()
    self.tic()

    # comparaison is not end, node debian11 <-> reference debian11 ==> new array
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    self.assertEquals(test_server.getValidationState(), 'validated')
    # comparaison is not end, new array <-> reference debian10 ==> new array2
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    self.assertEquals(test_server.getValidationState(), 'validated')
    # comparaison is end, can't compare new array2
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    self.assertEquals(test_server.getValidationState(), 'invalidated')
    server_uid_ndarray = np.array([7, 9, 10, 11])
    tmp_data_array = self.getPortalObject().data_array_module.newContent(portal_type='Data Array', title='%s-%s' % (server_publication_list[0],server_publication_list[1]))
    tmp_data_array.setCausality('data_product_module/test_server')
    tmp_data_array.initArray(shape=(server_uid_ndarray.size,), dtype='int64')
    tmp_data_array.setArray(server_uid_ndarray)
    tmp_data_array.setPublicationSectionList(server_publication_list)
    tmp_data_array.convertFile()
    self.tic()
    # comparaison is not end, node debian11 <-> reference debian11 ==> new array
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    self.assertEquals(test_server.getValidationState(), 'invalidated')
    # comparaison is end, new array is in reference debian10
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    self.assertEquals(test_server.getValidationState(), 'validated')

  def test_whole_process_from_data_stream_to_data_array_comparaison(self):
    request = self.portal.REQUEST
    request_dict = self._create_request_dict()
    for reference in request_dict:
      request.environ["REQUEST_METHOD"] = 'POST'
      request.set('reference', reference)
      request.set('data_chunk', request_dict[reference])
      self.portal.portal_ingestion_policies.metadata_upload.ingest()
    self.tic()


    data_stream_list = self.portal.portal_catalog(portal_type = 'Data Stream')
    self.assertEqual(len(data_stream_list), 3)

    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    data_array_list = self.portal.portal_catalog(portal_type='Data Array')
    self.assertEqual(len(data_array_list), 3)
    for reference in request_dict:
      data_array = self.portal.portal_catalog.getResultValue(
        portal_type='Data Array',
        reference='%' + reference)
      data_product = self.portal.portal_catalog.getResultValue(
        portal_type='Data Product',
        reference = reference)
      self.assertEqual(data_array.getPublicationSectionList(), data_product.getPublicationSectionList())
      self.assertEqual(data_array.getCausalityValue(), data_product)

    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    data_array_list = self.portal.portal_catalog(portal_type='Data Array')
    self.assertEqual(len(data_array_list), 4)
    last_data_array = self.portal.portal_catalog.getResultValue(
      portal_type='Data Array',
      simulation_state='converted')
    self.assertEqual(len(last_data_array.getPredecessorValueList()), 2)
    server_data_product = last_data_array.getCausalityValue()
    # Manually set to invalidate
    if server_data_product.getValidationState() != 'invalidated':
      server_data_product.invalidate()
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    data_array_list = self.portal.portal_catalog(portal_type='Data Array')
    self.assertEqual(len(data_array_list), 4)
    self.assertEqual(last_data_array.getSimulationState(), 'processed')
    self.assertEqual(server_data_product.getValidationState(), 'validated')

  def test_data_product_create_validate_data_supply(self):
    data_supply = self.data_product.DataProduct_createDataSupply(batch=1)
    data_supply.edit(
      source = 'organisation_module/server_node',
      source_section = 'organisation_module/server_node',
      destination = 'organisation_module/meta_destination',
      destination_section = 'organisation_module/meta_destination')
    self.tic()
    request = self.portal.REQUEST
    data_chunk = self._create_request_dict()['test_server']
    reference=self.data_product.getReference()

    request.environ["REQUEST_METHOD"] = 'POST'
    request.set('reference', reference)
    request.set('data_chunk', data_chunk)
    self.portal.portal_ingestion_policies.metadata_upload.ingest()
    self.tic()

    data_stream = self.portal.portal_catalog.getResultValue(
      portal_type = 'Data Stream',
      reference =  '%s-%s' % (reference, reference)
    )
    self.assertTrue(data_stream is not None)

  def test_data_product_create_validate_data_transformation(self):
    self.data_product.DataProduct_createDataTransformation(batch=1)
    self.tic()
    self.test_data_product_create_validate_data_supply()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()

    data_array_list = self.portal.portal_catalog(
      portal_type='Data Array'
    )
    self.assertEqual(len(data_array_list), 1)
    self.assertEqual(data_array_list[0].getCausalityValue(), self.data_product)

  def test_multi_data_array(self):
    request = self.portal.REQUEST
    request_dict = self._create_request_dict()
    for reference in request_dict:
      request.environ["REQUEST_METHOD"] = 'POST'
      request.set('reference', reference)
      request.set('data_chunk', request_dict[reference])
      self.portal.portal_ingestion_policies.metadata_upload.ingest()
    self.tic()


    data_stream_list = self.portal.portal_catalog(portal_type = 'Data Stream')
    self.assertEqual(len(data_stream_list), 3)

    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    # 2 references, 1 node
    data_array_list = self.portal.portal_catalog(portal_type='Data Array')
    self.assertEqual(len(data_array_list), 3)

    # 1 is created
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    data_array_list = self.portal.portal_catalog(portal_type='Data Array')
    self.assertEqual(len(data_array_list), 4)

    for data_array in data_array_list:
      self.assertEqual(data_array.getSimulationState(), 'processed')
    # everything is handleed, no more data array is created
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    data_array_list = self.portal.portal_catalog(portal_type='Data Array')
    self.assertEqual(len(data_array_list), 4)

    request = self.portal.REQUEST
    request_dict = self._create_request_dict()
    for reference in request_dict:
      request.environ["REQUEST_METHOD"] = 'POST'
      request.set('reference', reference)
      request.set('data_chunk', request_dict[reference])
      self.portal.portal_ingestion_policies.metadata_upload.ingest()
    self.tic()

    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    new_data_array_list = self.portal.portal_catalog(portal_type='Data Array')
    new_data_array_list = [x for x in new_data_array_list if x.getSimulationState() == 'converted']
    self.assertEqual(len(new_data_array_list), 3)
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()

  def test_multi_data_array_when_have_multi_data(self):
    request = self.portal.REQUEST
    request_dict = self._create_request_dict()
    for reference in request_dict:
      request.environ["REQUEST_METHOD"] = 'POST'
      request.set('reference', reference)
      request.set('data_chunk', request_dict[reference])
      self.portal.portal_ingestion_policies.metadata_upload.ingest()
    self.tic()
    for reference in request_dict:
      request.environ["REQUEST_METHOD"] = 'POST'
      request.set('reference', reference)
      request.set('data_chunk', request_dict[reference])
      self.portal.portal_ingestion_policies.metadata_upload.ingest()
    self.tic()
    data_stream_list = self.portal.portal_catalog(portal_type = 'Data Stream')
    self.assertEqual(len(data_stream_list), 3)

    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    # 2 references, 1 node
    data_array_list = self.portal.portal_catalog(portal_type='Data Array')
    self.assertEqual(len(data_array_list), 3)
    for array in data_array_list:
      self.assertEqual(array.getSimulationState(), 'converted')
    # still the same
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    # 2 references, 1 node
    data_array_list = self.portal.portal_catalog(portal_type='Data Array')
    self.assertEqual(len(data_array_list), 3)
    for array in data_array_list:
      self.assertEqual(array.getSimulationState(), 'converted')

    # 1 is created
    self.portal.portal_alarms.slapos_check_node_status.activeSense()
    self.tic()
    for array in data_array_list:
      self.assertEqual(array.getSimulationState(), 'processed')

    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    self.portal.portal_alarms.wendelin_handle_analysis.activeSense()
    self.tic()
    new_data_array_list = self.portal.portal_catalog(portal_type='Data Array')
    self.assertEqual(len(new_data_array_list), 7)
    self.tic()

