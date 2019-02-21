# coding=utf-8
# Copyright (c) 2015 EMC Corporation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import unicode_literals

import unittest

import ddt
import hamcrest as hc

import storops
from storops.unity.resource import import_session, remote_system, \
    replication_session, host
from storops_test.unity import rest_mock as mock

__author__ = 'Yong Huang'


def get_resource_config():
    resource_type = storops.ReplicationEndpointResourceTypeEnum.LUN
    return replication_session.UnityResourceConfig.to_embedded(
        pool_id='pool_1',
        is_thin_enabled=True,
        is_deduplication_enabled=True,
        is_compression_enabled=True,
        is_backup_only=True,
        size=1024,
        tiering_policy=storops.TieringPolicyEnum.AUTOTIER,
        request_id='request_1',
        src_id='src_1',
        name='resource_config_1',
        default_sp=storops.NodeEnum.SPA,
        replication_resource_type=resource_type
    )


@ddt.ddt
class UnityImportSessionTest(unittest.TestCase):
    @mock.patch_rest
    def test_get_properties(self):
        sess = import_session.UnityImportSession.get(cli=mock.t_rest(),
                                                     _id='import_65558')
        element_import_0 = sess.element_imports[0]
        hc.assert_that(sess.id, hc.equal_to('import_65558'))
        hc.assert_that(sess.state,
                       hc.equal_to(storops.ImportStateEnum.READY_TO_CUTOVER))
        hc.assert_that(sess.status,
                       hc.equal_to(
                           storops.ImportOpStatusEnum.READY_TO_CUTOVER))
        hc.assert_that(sess.operational_status[0],
                       hc.equal_to(
                           storops.ImportOpStatusEnum.READY_TO_CUTOVER))
        hc.assert_that(sess.type, hc.equal_to(storops.ImportTypeEnum.BLOCK))
        hc.assert_that(sess.resource_type,
                       hc.equal_to(storops.RemoteObjectTypeEnum.LUN))
        hc.assert_that(sess.target_resource_type,
                       hc.equal_to(storops.PoolConsumerTypeEnum.LUN))
        hc.assert_that(sess.instance_id, hc.equal_to('import_65558'))
        hc.assert_that(sess.name, hc.equal_to(
            'Import_APM00152904558_541_20190305062151.415258+000'))
        hc.assert_that(sess.health.value, hc.equal_to(storops.HealthEnum.OK))
        hc.assert_that(sess.src_resource.res_id, hc.equal_to('541'))
        hc.assert_that(sess.src_resource.name, hc.equal_to('lun-liangr'))
        hc.assert_that(sess.src_resource.system.id, hc.equal_to('RS_65557'))
        hc.assert_that(sess.target_resource.res_id, hc.equal_to(
            '60:06:01:60:74:E0:3A:00:80:15:7E:5C:EF:22:24:08'))
        hc.assert_that(sess.target_resource.name, hc.equal_to('lun-liangr-1'))
        hc.assert_that(sess.target_resource.system.id, hc.equal_to(
            'RS_65557'))
        hc.assert_that(len(sess.element_imports), hc.equal_to(1))
        hc.assert_that(element_import_0.src_id, hc.equal_to(
            'APM00152904558_60:06:01:60:12:90:38:00:F7:99:07:16:BE:DF:E7:11'))
        hc.assert_that(element_import_0.src_name, hc.equal_to('lun-liangr'))
        hc.assert_that(element_import_0.tgt_id, hc.equal_to('sv_2564'))
        hc.assert_that(element_import_0.tgt_name, hc.equal_to('lun-liangr-1'))
        hc.assert_that(sess.throttle, hc.equal_to(False))
        hc.assert_that(sess.remaining_data_size, hc.equal_to(0))
        hc.assert_that(sess.cutover_threshold, hc.equal_to(5))
        hc.assert_that(sess.remaining_data_percent, hc.equal_to(0))
        hc.assert_that(sess.estimated_cutover_window, hc.equal_to(0))
        hc.assert_that(sess.remote_system.id, hc.equal_to('RS_65557'))

    @mock.patch_rest
    def test_get_collection(self):
        sess_list = import_session.UnityImportSessionList.get(
            mock.t_rest())
        hc.assert_that(len(sess_list), hc.equal_to(3))
        hc.assert_that([sess.id for sess in sess_list],
                       hc.equal_to(
                           ['import_65558', 'import_65560', 'import_65562']))

    rc = get_resource_config()

    @mock.patch_rest
    @ddt.data(
        {'remote_sys_id': 'RS_65557',
         'src_resource_id': 'resource_1',
         'dst_resource_config': rc,
         'dst_resource_element_configs': [rc],
         'import_as_vmware_datastore': True,
         'throttle': False,
         'hosts':
             [host.UnityHost(_id='Host_27', cli=mock.t_rest())],
         'cutover_threshold': 80,
         'name': 'test_import_session_1'},
        {'remote_sys_id': 'RS_65557',
         'src_resource_id': 'resource_1',
         'dst_resource_config': rc,
         'dst_resource_element_configs': None,
         'import_as_vmware_datastore': None,
         'throttle': None,
         'hosts': None,
         'cutover_threshold': None,
         'name': None})
    @ddt.unpack
    def test_create_block_import(
            self, remote_sys_id, src_resource_id, dst_resource_config,
            dst_resource_element_configs=None,
            import_as_vmware_datastore=None,
            throttle=None, hosts=None, cutover_threshold=None, name=None):
        remote_sys = remote_system.UnityRemoteSystem(_id=remote_sys_id,
                                                     cli=mock.t_rest())
        src_resource = replication_session.UnityResourceInfo.to_embedded(
            res_id=src_resource_id, name=src_resource_id.upper(),
            system=remote_sys)
        sess = import_session.UnityImportSession(_id='import_65558',
                                                 cli=mock.t_rest())
        resp = sess.create_block_import(
            cli=mock.t_rest(),
            remote_system=remote_sys,
            src_resource=src_resource,
            dst_resource_config=dst_resource_config,
            dst_resource_element_configs=dst_resource_element_configs,
            import_as_vmware_datastore=import_as_vmware_datastore,
            throttle=throttle, hosts=hosts,
            cutover_threshold=cutover_threshold,
            name=name)
        hc.assert_that(resp.id, hc.equal_to('import_65564'))

    @mock.patch_rest
    @ddt.data(
        {'throttle': True,
         'name': 'import_session_1',
         'cutover_threshold': 80,
         'src_local_cifs_admin_username': 'user_1',
         'src_local_cifs_admin_passwd': 'passwd_1'},
        {'throttle': None,
         'name': None,
         'cutover_threshold': None,
         'src_local_cifs_admin_username': None,
         'src_local_cifs_admin_passwd': None})
    @ddt.unpack
    def test_modify(self, throttle=None, name=None, cutover_threshold=None,
                    src_local_cifs_admin_username=None,
                    src_local_cifs_admin_passwd=None):
        sess = import_session.UnityImportSession(_id='import_65558',
                                                 cli=mock.t_rest())
        resp = sess.modify(
            throttle=throttle, name=name,
            cutover_threshold=cutover_threshold,
            src_local_cifs_admin_username=src_local_cifs_admin_username,
            src_local_cifs_admin_passwd=src_local_cifs_admin_passwd)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    @ddt.data(
        {'test_facility_code': 'test_facility_code_1'},
        {'test_facility_code': None})
    @ddt.unpack
    def test_pause(self, test_facility_code=None):
        sess = import_session.UnityImportSession(_id='import_65558',
                                                 cli=mock.t_rest())
        resp = sess.pause(test_facility_code=test_facility_code)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    def test_resume(self):
        sess = import_session.UnityImportSession(_id='import_65558',
                                                 cli=mock.t_rest())
        resp = sess.resume()
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    @ddt.data(
        {'cifs_server_info':
            import_session.UnityCifsServerInfo.to_embedded(
                name='cifs_server_1', description='CIFS Server 1',
                netbios_name='smb_server_1', domain='domain_1',
                workgroup='group_1', is_standalone=True,
                cifs_username='cifs_user_1'),
            'domain_username': 'ad_user_1',
            'domain_password': 'ad_passwd_1'},
        {'cifs_server_info': None,
         'domain_username': None,
         'domain_password': None})
    @ddt.unpack
    def test_cutover(self, cifs_server_info=None, domain_username=None,
                     domain_password=None):
        sess = import_session.UnityImportSession(_id='import_65558',
                                                 cli=mock.t_rest())
        resp = sess.cutover(cifs_server_info=cifs_server_info,
                            domain_username=domain_username,
                            domain_password=domain_password)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    def test_commit(self):
        sess = import_session.UnityImportSession(_id='import_65558',
                                                 cli=mock.t_rest())
        resp = sess.commit()
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    @ddt.data(
        {'domain_username': 'ad_user_1', 'domain_password': 'ad_passwd_1'},
        {'domain_username': None, 'domain_password': None})
    @ddt.unpack
    def test_cancel(self, domain_username=None, domain_password=None):
        sess = import_session.UnityImportSession(_id='import_65558',
                                                 cli=mock.t_rest())
        resp = sess.cancel(domain_username=domain_username,
                           domain_password=domain_password)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    def test_delete(self):
        sess = import_session.UnityImportSession(_id='import_65558',
                                                 cli=mock.t_rest())
        resp = sess.delete()
        hc.assert_that(resp.is_ok(), hc.equal_to(True))
