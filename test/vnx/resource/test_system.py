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

import logging
from unittest import TestCase

from hamcrest import assert_that, equal_to, none, instance_of, raises, is_not

from storops import VNXSystem
from storops.exception import VNXDeleteHbaNotFoundError, VNXCredentialError, \
    VNXUserNameInUseError, VNXBackendError, VNXSetArrayNameError
from storops.lib.common import instance_cache
from storops.lib.resource import ResourceListCollection
from storops.vnx.enums import VNXLunType, VNXPortType, VNXSPEnum, \
    VNXUserRoleEnum
from storops.vnx.resource.cifs_server import CifsDomain
from storops.vnx.resource.disk import VNXDisk
from storops.vnx.resource.lun import VNXLun
from storops.vnx.resource.mirror_view import VNXMirrorViewList
from storops.vnx.resource.mover import VNXMoverList
from storops.vnx.resource.port import VNXSPPortList, VNXConnectionPortList
from storops.vnx.resource.system import VNXAgent
from storops.vnx.resource.system import VNXArrayName
from storops.vnx.resource.vdm import VNXVdmList
from storops.vnx.resource.vnx_domain import VNXDomainMemberList, \
    VNXStorageProcessor
from test.vnx.cli_mock import patch_cli, t_vnx, t_cli
from test.vnx.nas_mock import patch_post
from test.vnx.resource.verifiers import verify_pool_0

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class VNXSystemTest(TestCase):
    @patch_cli()
    def setUp(self):
        self.vnx = t_vnx()

    @patch_cli
    def test_properties(self):
        assert_that(self.vnx.model, equal_to("VNX5800"))
        assert_that(self.vnx.model_type, equal_to('Rackmount'))
        assert_that(self.vnx.serial, equal_to('APM00153042305'))
        assert_that(self.vnx.agent_rev, equal_to('7.33.8 (2.97)'))
        assert_that(self.vnx.name, equal_to('IT_IS_ARR_NAME'))
        assert_that(self.vnx.revision, equal_to('05.33.008.3.297'))
        assert_that(self.vnx.existed, equal_to(True))

    @patch_cli
    def test_get_pool_list(self):
        pool_list = self.vnx.get_pool()
        assert_that(len(pool_list), equal_to(5))

    @patch_cli
    def test_get_pool(self):
        pool = self.vnx.get_pool(pool_id=0)
        verify_pool_0(pool)

    @patch_cli
    def test_member_ips(self):
        vnx = VNXSystem('10.244.211.30', heartbeat_interval=0)
        assert_that(vnx.spa_ip, equal_to('192.168.1.52'))
        assert_that(vnx.spb_ip, equal_to('192.168.1.53'))
        assert_that(vnx.control_station_ip, equal_to('10.244.211.32'))

    @patch_cli
    def test_get_snap(self):
        snaps = self.vnx.get_snap()
        assert_that(len(snaps), equal_to(47))

        snap = self.vnx.get_snap('gan_snap')
        assert_that(snap.creation_time, equal_to('05/24/13 20:06:12'))

    @patch_cli
    def test_get_migration_session_list(self):
        ms_list = self.vnx.get_migration_session()
        assert_that(len(ms_list), equal_to(2))

    @patch_cli
    def test_get_migration_session(self):
        source = VNXLun(lun_id=0)
        ms = self.vnx.get_migration_session(source)
        assert_that(ms.existed, equal_to(True))

    @patch_cli
    def test_get_snap_lun(self):
        snap_luns = self.vnx.get_lun(lun_type=VNXLunType.SNAP_MOUNT_POINT)
        assert_that(len(snap_luns), equal_to(45))
        for snap_lun in snap_luns:
            assert_that(snap_lun.is_snap_mount_point, equal_to(True))

    @patch_cli
    def test_pool_feature(self):
        pf = self.vnx.get_pool_feature()
        assert_that(pf.max_pool_luns, equal_to(2100))
        assert_that(pf.total_pool_luns, equal_to(2))

    @patch_cli
    def test_pool_feature_no_poll(self):
        pf = self.vnx.get_pool_feature(False)
        assert_that(pf.max_pool_luns, equal_to(2100))

    @patch_cli
    def test_sp_port(self):
        assert_that(len(self.vnx.get_sp_port()), equal_to(32))

    @patch_cli
    def test_connection_port(self):
        assert_that(len(self.vnx.get_connection_port()), equal_to(20))

    @patch_cli
    def test_is_feature_enabled(self):
        assert_that(self.vnx.is_compression_enabled(), equal_to(True))
        assert_that(self.vnx.is_snap_enabled(), equal_to(True))
        assert_that(self.vnx.is_dedup_enabled(), equal_to(True))
        assert_that(self.vnx.is_mirror_view_async_enabled(), equal_to(True))
        assert_that(self.vnx.is_mirror_view_sync_enabled(), equal_to(True))
        assert_that(self.vnx.is_mirror_view_enabled(), equal_to(True))
        assert_that(self.vnx.is_thin_enabled(), equal_to(True))
        assert_that(self.vnx.is_sancopy_enabled(), equal_to(True))
        assert_that(self.vnx.is_auto_tiering_enabled(), equal_to(True))
        assert_that(self.vnx.is_fast_cache_enabled(), equal_to(True))

    @patch_cli
    def test_available_disks(self):
        disks = self.vnx.get_available_disks()
        assert_that(len(disks), equal_to(5))
        for disk in disks:
            assert_that(disk, instance_of(VNXDisk))
            assert_that(disk.existed, equal_to(True))

    @patch_cli(mock_map={'-np_domain': 'domain_-list_no_cs.txt'})
    def test_member_ip_no_cs(self):
        vnx = VNXSystem('1.1.1.1', heartbeat_interval=0)
        assert_that(vnx.control_station_ip, none())

    @patch_cli
    def test_get_fc_port_all(self):
        ports = self.vnx.get_fc_port()
        assert_that(ports, instance_of(VNXSPPortList))
        assert_that(len(ports), equal_to(28))
        for port in ports:
            assert_that(port.type, equal_to(VNXPortType.FC))

    @patch_cli
    def test_get_fc_port_filtered_to_single(self):
        ports = self.vnx.get_fc_port(sp=VNXSPEnum.SP_A, port_id=1)
        assert_that(len(ports), equal_to(1))
        port = ports[0]
        assert_that(port.sp, equal_to(VNXSPEnum.SP_A))
        assert_that(port.port_id, equal_to(1))
        assert_that(port.type, equal_to(VNXPortType.FC))

    @patch_cli
    def test_get_fc_port_filtered_by_id(self):
        ports = self.vnx.get_fc_port(port_id=1)
        assert_that(ports, instance_of(VNXSPPortList))
        assert_that(len(ports), equal_to(2))

    @patch_cli
    def test_get_iscsi_port_all(self):
        ports = self.vnx.get_iscsi_port()
        assert_that(ports, instance_of(VNXConnectionPortList))
        assert_that(len(ports), equal_to(16))
        for port in ports:
            assert_that(port.type, equal_to(VNXPortType.ISCSI))

    @patch_cli
    def test_get_iscsi_port_with_ip(self):
        ports = self.vnx.get_iscsi_port(has_ip=True)
        assert_that(ports, instance_of(VNXConnectionPortList))
        assert_that(len(ports), equal_to(4))

    @patch_cli
    def test_get_iscsi_port_without_ip(self):
        ports = self.vnx.get_iscsi_port(has_ip=False)
        assert_that(ports, instance_of(VNXConnectionPortList))
        assert_that(len(ports), equal_to(12))

    @patch_cli
    def test_get_iscsi_port_filtered_type_not_match(self):
        port = self.vnx.get_iscsi_port(sp=VNXSPEnum.SP_A, port_id=8,
                                       vport_id=0)
        assert_that(port, none())

    @patch_cli
    def test_get_iscsi_port_filtered_type_match(self):
        port = self.vnx.get_iscsi_port(sp=VNXSPEnum.SP_A, port_id=5,
                                       vport_id=0)
        assert_that(port.sp, equal_to(VNXSPEnum.SP_A))
        assert_that(port.port_id, equal_to(5))
        assert_that(port.vport_id, equal_to(0))

    @patch_cli
    def test_get_iscsi_port_filtered_without_vport(self):
        ports = self.vnx.get_iscsi_port(sp=VNXSPEnum.SP_B, port_id=10)
        port = ports[0]
        assert_that(port.sp, equal_to(VNXSPEnum.SP_B))
        assert_that(port.port_id, equal_to(10))
        assert_that(port.vport_id, none())

    @patch_cli
    def test_get_iscsi_port_filtered_no_vport(self):
        port = self.vnx.get_iscsi_port(sp=VNXSPEnum.SP_B, port_id=10,
                                       vport_id=0)
        assert_that(port, none())

    @patch_cli
    def test_get_iscsi_port_filtered_by_vport(self):
        ports = self.vnx.get_iscsi_port(vport_id=0)
        assert_that(ports, instance_of(VNXConnectionPortList))
        assert_that(len(ports), equal_to(4))

    @patch_cli
    def test_get_fcoe_port_all(self):
        ports = self.vnx.get_fcoe_port()
        assert_that(ports, instance_of(VNXConnectionPortList))
        assert_that(len(ports), equal_to(4))
        for port in ports:
            assert_that(port.type, equal_to(VNXPortType.FCOE))

    @patch_cli
    def test_get_fcoe_port_filtered_to_single(self):
        port = self.vnx.get_fcoe_port(sp=VNXSPEnum.SP_A, port_id=6,
                                      vport_id=0)
        assert_that(port.sp, equal_to(VNXSPEnum.SP_A))
        assert_that(port.port_id, equal_to(6))
        assert_that(port.vport_id, equal_to(0))
        assert_that(port.type, equal_to(VNXPortType.FCOE))

    @patch_cli
    def test_get_fcoe_port_filtered_by_sp(self):
        ports = self.vnx.get_fcoe_port(sp=VNXSPEnum.SP_B)
        assert_that(ports, instance_of(VNXConnectionPortList))
        assert_that(len(ports), equal_to(2))

    @patch_cli
    def test_delete_hba_already_removed(self):
        def f():
            uid = '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:01'
            self.vnx.delete_hba(uid)

        assert_that(f, raises(VNXDeleteHbaNotFoundError))

    @patch_cli
    def test_get_block_users(self):
        users = self.vnx.get_block_user()
        assert_that(len(users), equal_to(2))

    @patch_cli
    def test_create_user_existed(self):
        def f():
            self.vnx.create_block_user('b', 'b', role=VNXUserRoleEnum.OPERATOR)

        assert_that(f, raises(VNXUserNameInUseError, 'failed'))

    @patch_cli
    def test_get_mirror_view(self):
        mv_list = self.vnx.get_mirror_view()
        assert_that(mv_list, instance_of(VNXMirrorViewList))
        assert_that(len(mv_list), equal_to(4))

    @patch_cli
    def test_create_mirror_view(self):
        lun = VNXLun(245)
        mv = self.vnx.create_mirror_view('mv0', lun)
        assert_that(mv.state, equal_to('Active'))

    @patch_cli(output='credential_error.txt')
    def test_credential_error(self):
        def f():
            return VNXSystem('10.244.211.30', heartbeat_interval=0).spa_ip

        assert_that(f, raises(VNXCredentialError, 'invalid username'))

    @patch_cli
    def test_get_capacity(self):
        capacity = self.vnx.get_capacity()
        assert_that(capacity.total, equal_to(178269.891))

    @property
    @patch_cli
    @instance_cache
    def vnx_file(self):
        log.info('init file mock connection: {}.'.format(self.vnx._file_cli))
        log.info('mock cs ip: {}.'.format(self.vnx.control_station_ip))
        return self.vnx

    @patch_post
    def test_get_file_system(self):
        assert_that(len(self.vnx_file.get_file_system()), equal_to(25))

    @patch_post
    def test_get_nas_pool(self):
        assert_that(len(self.vnx_file.get_nas_pool()), equal_to(6))

    @patch_post
    def test_get_cifs_server(self):
        assert_that(len(self.vnx_file.get_cifs_server()), equal_to(4))

    @patch_post
    def test_create_cifs_server(self):
        def f():
            domain = CifsDomain('test.dev')
            self.vnx_file.create_cifs_server('test', 1, domain=domain)

        assert_that(f, raises(VNXBackendError, 'default NT server'))

    @patch_post
    def test_get_cifs_share(self):
        assert_that(len(self.vnx_file.get_cifs_share()), equal_to(16))

    @patch_post
    def test_get_physical_data_mover(self):
        dm_list = self.vnx_file.get_mover()
        assert_that(dm_list, instance_of(VNXMoverList))
        assert_that(len(dm_list), equal_to(2))

    @patch_post
    def test_get_vdm(self):
        vdm_list = self.vnx_file.get_mover(is_vdm=True)
        assert_that(vdm_list, instance_of(VNXVdmList))
        assert_that(len(vdm_list), equal_to(2))

    @patch_post
    def test_file_system_snap(self):
        snap = self.vnx_file.get_file_system_snap()
        assert_that(len(snap), equal_to(2))

    @patch_post
    def test_get_nfs_share(self):
        assert_that(len(self.vnx_file.get_nfs_share()), equal_to(26))

    @patch_cli
    def test_domain_properties(self):
        assert_that(self.vnx.domain, instance_of(VNXDomainMemberList))

    @patch_cli
    def test_alive_sp_ip(self):
        log.debug('sp ips {}, {}'.format(self.vnx.spa_ip, self.vnx.spb_ip))
        assert_that(self.vnx.alive_sp_ip, equal_to('10.244.211.30'))

    @patch_cli
    def test_get_sp(self):
        assert_that(len(self.vnx.get_sp()), equal_to(2))
        assert_that(self.vnx.spa, instance_of(VNXStorageProcessor))
        assert_that(self.vnx.spa.name, equal_to('A'))
        assert_that(self.vnx.spa.signature, equal_to(4022290))
        assert_that(self.vnx.spb, instance_of(VNXStorageProcessor))
        assert_that(self.vnx.spb.name, equal_to('B'))
        assert_that(self.vnx.spb.signature, equal_to(4022287))

    @patch_cli
    def test_create_pool(self):
        pool = self.vnx.create_pool('Pool4File')
        assert_that(pool.existed, equal_to(True))
        assert_that(pool.name, equal_to('Pool4File'))

    @patch_cli
    def test_get_host(self):
        host = self.vnx.get_host('ubuntu14')
        assert_that(host.name, equal_to('ubuntu14'))
        assert_that(host.existed, equal_to(True))
        assert_that(len(host.connections), equal_to(4))

    @patch_cli
    def test_enable_perf_stats_default(self):
        vnx = VNXSystem('10.244.211.30')
        clz_list = vnx.enable_perf_stats()
        assert_that(len(clz_list), equal_to(6))
        assert_that(vnx.is_perf_stats_enabled(), equal_to(True))

        vnx.disable_perf_stats()
        assert_that(vnx.is_perf_stats_enabled(), equal_to(False))

    @patch_cli
    def test_enable_perf_stats_filtered(self):
        vnx = VNXSystem('10.244.211.30')
        clz_list = vnx.enable_perf_stats([VNXLun, VNXDisk])
        assert_that(len(clz_list), equal_to(2))
        vnx.disable_perf_stats()

    @patch_cli
    def test_get_rsc_list_2_returns_different_instances(self):
        ret1 = self.vnx.get_rsc_list_2()
        ret2 = self.vnx.get_rsc_list_2()
        assert_that(ret1, is_not(equal_to(ret2)))

    @patch_cli
    def test_enable_persist_perf_stats(self):
        vnx = VNXSystem('10.244.211.30')
        vnx.enable_persist_perf_stats()
        assert_that(vnx.is_perf_stats_persisted(), equal_to(True))

        vnx.disable_persist_perf_stats()
        assert_that(vnx.is_perf_stats_persisted(), equal_to(False))

    @patch_cli
    def test_collect_perf_record(self):
        record = self.vnx.collect_perf_record([VNXLun, VNXDisk])
        assert_that(record, instance_of(ResourceListCollection))
        assert_that(len(record), equal_to(2))


class VNXArrayNameTest(TestCase):
    @patch_cli
    def test_get(self):
        array_name = VNXArrayName(t_cli())
        assert_that(array_name.name, equal_to('IT_IS_ARR_NAME'))

    @patch_cli
    def test_set_too_long(self):
        def f():
            array_name = VNXArrayName(t_cli())
            array_name.set_name(
                '123456789_123456789_123456789_123456789'
                '_123456789_123456789_123456789')

        assert_that(f, raises(VNXSetArrayNameError, 'is 64'))


class VNXAgentTest(TestCase):
    @patch_cli
    def test_get(self):
        agent = VNXAgent(t_cli())
        assert_that(agent.revision, equal_to('05.33.008.3.297'))
