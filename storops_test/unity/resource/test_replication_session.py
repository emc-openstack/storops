# Copyright (c) 2018 Dell Inc. or its subsidiaries.
# All Rights Reserved.
#
#    Licensed under the Apache License, Veriion 2.0 (the "License"); you may
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
import unittest

import ddt
import hamcrest as hc

import storops
from storops.unity.resource import health, replication_session, \
    remote_system, remote_interface
from storops_test.unity import rest_mock as mock

__author__ = 'Ryan Liang'


@ddt.ddt
class UnityReplicationSessionTest(unittest.TestCase):
    @mock.patch_rest
    def test_get_properties(self):
        rs = replication_session.UnityReplicationSession.get(
            cli=mock.t_rest(), _id='42949675124_FNM00150600267_0000'
                                   '_42949678638_FNM00152000052_0000')
        hc.assert_that(rs.current_transfer_est_remain_time, hc.equal_to(0))
        hc.assert_that(rs.daily_snap_replication_policy,
                       hc.instance_of(
                           replication_session.UnitySnapReplicationPolicy))
        hc.assert_that(rs.daily_snap_replication_policy.is_replicating_snaps,
                       hc.equal_to(False))
        hc.assert_that(rs.dst_resource_id, hc.equal_to('sv_3'))
        hc.assert_that(rs.dst_spa_interface,
                       hc.instance_of(remote_interface.UnityRemoteInterface))
        hc.assert_that(rs.dst_spa_interface.id,
                       hc.equal_to('FNM00152000052:if_7'))
        hc.assert_that(rs.dst_spb_interface,
                       hc.instance_of(remote_interface.UnityRemoteInterface))
        hc.assert_that(rs.dst_spb_interface.id,
                       hc.equal_to('FNM00152000052:if_6'))
        hc.assert_that(rs.dst_status,
                       hc.equal_to(storops.ReplicationSessionStatusEnum.OK))
        hc.assert_that(rs.health, hc.instance_of(health.UnityHealth))
        hc.assert_that(rs.health.value, hc.equal_to(storops.HealthEnum.OK))
        hc.assert_that(rs.hourly_snap_replication_policy,
                       hc.instance_of(
                           replication_session.UnitySnapReplicationPolicy))
        hc.assert_that(rs.hourly_snap_replication_policy.is_replicating_snaps,
                       hc.equal_to(False))
        hc.assert_that(rs.id, hc.equal_to(
            '42949675124_FNM00150600267_0000_42949678638_FNM00152000052_0000'))
        hc.assert_that(str(rs.last_sync_time),
                       hc.equal_to('2018-12-07 09:27:47+00:00'))
        hc.assert_that(rs.local_role, hc.equal_to(
            storops.ReplicationSessionReplicationRoleEnum.SOURCE))
        hc.assert_that(rs.max_time_out_of_sync, hc.equal_to(60))
        hc.assert_that(rs.members, hc.none())
        hc.assert_that(rs.name, hc.equal_to(
            'rep_sess_sv_1876_sv_3_FNM00150600267_FNM00152000052'))
        hc.assert_that(rs.network_status, hc.equal_to(
            storops.ReplicationSessionNetworkStatusEnum.OK))
        hc.assert_that(rs.remote_system,
                       hc.instance_of(remote_system.UnityRemoteSystem))
        hc.assert_that(rs.remote_system.id, hc.equal_to('RS_4'))
        hc.assert_that(rs.replication_resource_type, hc.equal_to(
            storops.ReplicationEndpointResourceTypeEnum.LUN))
        hc.assert_that(rs.src_resource_id, hc.equal_to('sv_1876'))
        hc.assert_that(rs.src_spa_interface,
                       hc.instance_of(remote_interface.UnityRemoteInterface))
        hc.assert_that(rs.src_spa_interface.id,
                       hc.equal_to('FNM00150600267:if_10'))
        hc.assert_that(rs.src_spb_interface,
                       hc.instance_of(remote_interface.UnityRemoteInterface))
        hc.assert_that(rs.src_spb_interface.id,
                       hc.equal_to('FNM00150600267:if_11'))
        hc.assert_that(rs.src_status,
                       hc.equal_to(storops.ReplicationSessionStatusEnum.OK))
        hc.assert_that(rs.status, hc.equal_to(
            storops.ReplicationOpStatusEnum.AUTO_SYNC_CONFIGURED))
        hc.assert_that(rs.sync_progress, hc.equal_to(0))
        hc.assert_that(rs.sync_state, hc.equal_to(
            storops.ReplicationSessionSyncStateEnum.IDLE))

    @mock.patch_rest
    def test_get_collection(self):
        rs_list = replication_session.UnityReplicationSessionList.get(
            mock.t_rest())
        hc.assert_that(len(rs_list), hc.equal_to(2))
        hc.assert_that(
            [rs.id for rs in rs_list],
            hc.equal_to(['42949675116_FNM00150600267_0000'
                         '_42949675117_FNM00150600267_0000',
                         '42949675124_FNM00150600267_0000'
                         '_42949678638_FNM00152000052_0000']))

    @mock.patch_rest
    @ddt.data(
        {'src_resource_id': 'sv_2498', 'dst_resource_id': 'sv_5',
         'max_time_out_of_sync': 60, 'name': 'remote-sv_2498-sv_5',
         'members': None, 'auto_initiate': False,
         'hourly_snap_replication_policy':
             replication_session.UnitySnapReplicationPolicy.to_embedded(
                 is_replicating_snaps=False),
         'daily_snap_replication_policy':
             replication_session.UnitySnapReplicationPolicy.to_embedded(
                 is_replicating_snaps=True, is_retention_same_as_source=False,
                 is_auto_delete=False, retention_duration=3600),
         'replicate_existing_snaps': False, 'remote_sys': 'RS_4',
         'src_spa_interface': 'FNM00152000052:if_7',
         'src_spb_interface': 'FNM00152000052:if_6',
         'dst_spa_interface': 'FNM00150600267:if_10',
         'dst_spb_interface': 'FNM00150600267:if_11'},
        {'src_resource_id': 'sv_2498', 'dst_resource_id': 'sv_5',
         'max_time_out_of_sync': 60, 'name': None,
         'members': None, 'auto_initiate': None,
         'hourly_snap_replication_policy': None,
         'daily_snap_replication_policy': None,
         'replicate_existing_snaps': None, 'remote_sys': None,
         'src_spa_interface': None, 'src_spb_interface': None,
         'dst_spa_interface': None, 'dst_spb_interface': None})
    @ddt.unpack
    def test_create(self, src_resource_id, dst_resource_id,
                    max_time_out_of_sync, name, members,
                    auto_initiate, hourly_snap_replication_policy,
                    daily_snap_replication_policy,
                    replicate_existing_snaps, remote_sys,
                    src_spa_interface, src_spb_interface,
                    dst_spa_interface, dst_spb_interface):

        if remote_sys:
            remote_sys = remote_system.UnityRemoteSystem(_id=remote_sys,
                                                         cli=mock.t_rest())
        if src_spa_interface:
            src_spa_interface = remote_interface.UnityRemoteInterface(
                _id=src_spa_interface, cli=mock.t_rest())
        if src_spb_interface:
            src_spb_interface = remote_interface.UnityRemoteInterface(
                _id=src_spb_interface, cli=mock.t_rest())
        if dst_spa_interface:
            dst_spa_interface = remote_interface.UnityRemoteInterface(
                _id=dst_spa_interface, cli=mock.t_rest())
        if dst_spb_interface:
            dst_spb_interface = remote_interface.UnityRemoteInterface(
                _id=dst_spb_interface, cli=mock.t_rest())
        rs = replication_session.UnityReplicationSession.create(
            mock.t_rest(), src_resource_id, dst_resource_id,
            max_time_out_of_sync, name=name, members=members,
            auto_initiate=auto_initiate,
            hourly_snap_replication_policy=hourly_snap_replication_policy,
            daily_snap_replication_policy=daily_snap_replication_policy,
            replicate_existing_snaps=replicate_existing_snaps,
            remote_system=remote_sys,
            src_spa_interface=src_spa_interface,
            src_spb_interface=src_spb_interface,
            dst_spa_interface=dst_spa_interface,
            dst_spb_interface=dst_spb_interface)
        hc.assert_that(rs.id, hc.equal_to(
            '42949675780_FNM00150600267_0000_42949678642_FNM00152000052_0000'))

    @mock.patch_rest
    @ddt.data(
        {'src_resource_id': 'sv_1876',
         'dst_resource_config':
             replication_session.UnityResourceConfig.to_embedded(
                 pool_id='pool_2', request_id='lun-rep-src3-liangr',
                 name='lun-rep-src3-liangr', is_thin_enabled=True,
                 size=10737418240,
                 tiering_policy=storops.TieringPolicyEnum.AUTOTIER_HIGH,
                 is_deduplication_enabled=False, is_compression_enabled=False),
         'max_time_out_of_sync': 60, 'name': 'remote-rep3',
         'remote_sys': 'RS_4',
         'src_spa_interface': 'FNM00152000052:if_7',
         'src_spb_interface': 'FNM00152000052:if_6',
         'dst_spa_interface': 'FNM00150600267:if_10',
         'dst_spb_interface': 'FNM00150600267:if_11',
         'dst_resource_element_configs': None, 'auto_initiate': False,
         'hourly_snap_replication_policy':
             replication_session.UnitySnapReplicationPolicy.to_embedded(
                 is_replicating_snaps=False),
         'daily_snap_replication_policy':
             replication_session.UnitySnapReplicationPolicy.to_embedded(
                 is_replicating_snaps=True, is_retention_same_as_source=False,
                 is_auto_delete=False, retention_duration=3600),
         'replicate_existing_snaps': False},
        {'src_resource_id': 'sv_1876',
         'dst_resource_config':
             replication_session.UnityResourceConfig.to_embedded(
                 pool_id='pool_2', request_id='lun-rep-src3-liangr',
                 name='lun-rep-src3-liangr', is_thin_enabled=True,
                 size=10737418240,
                 tiering_policy=storops.TieringPolicyEnum.AUTOTIER_HIGH,
                 is_deduplication_enabled=False, is_compression_enabled=False),
         'max_time_out_of_sync': 60, 'name': None, 'remote_sys': None,
         'src_spa_interface': None, 'src_spb_interface': None,
         'dst_spa_interface': None, 'dst_spb_interface': None,
         'dst_resource_element_configs': None, 'auto_initiate': None,
         'hourly_snap_replication_policy': None,
         'daily_snap_replication_policy': None,
         'replicate_existing_snaps': None})
    @ddt.unpack
    def test_create_with_dst_resource_provisioning(
            self, src_resource_id, dst_resource_config,
            max_time_out_of_sync, name=None, remote_sys=None,
            src_spa_interface=None, src_spb_interface=None,
            dst_spa_interface=None, dst_spb_interface=None,
            dst_resource_element_configs=None, auto_initiate=None,
            hourly_snap_replication_policy=None,
            daily_snap_replication_policy=None,
            replicate_existing_snaps=None):

        if remote_sys:
            remote_sys = remote_system.UnityRemoteSystem(_id=remote_sys,
                                                         cli=mock.t_rest())
        if src_spa_interface:
            src_spa_interface = remote_interface.UnityRemoteInterface(
                _id=src_spa_interface, cli=mock.t_rest())
        if src_spb_interface:
            src_spb_interface = remote_interface.UnityRemoteInterface(
                _id=src_spb_interface, cli=mock.t_rest())
        if dst_spa_interface:
            dst_spa_interface = remote_interface.UnityRemoteInterface(
                _id=dst_spa_interface, cli=mock.t_rest())
        if dst_spb_interface:
            dst_spb_interface = remote_interface.UnityRemoteInterface(
                _id=dst_spb_interface, cli=mock.t_rest())
        _cls = replication_session.UnityReplicationSession
        rs = _cls.create_with_dst_resource_provisioning(
            mock.t_rest(), src_resource_id, dst_resource_config,
            max_time_out_of_sync, name=name, remote_system=remote_sys,
            src_spa_interface=src_spa_interface,
            src_spb_interface=src_spb_interface,
            dst_spa_interface=dst_spa_interface,
            dst_spb_interface=dst_spb_interface,
            dst_resource_element_configs=dst_resource_element_configs,
            auto_initiate=auto_initiate,
            hourly_snap_replication_policy=hourly_snap_replication_policy,
            daily_snap_replication_policy=daily_snap_replication_policy,
            replicate_existing_snaps=replicate_existing_snaps)
        hc.assert_that(rs.id, hc.equal_to(
            '42949675780_FNM00150600267_0000_42949678642_FNM00152000052_0000'))

    @mock.patch_rest
    @ddt.data(
        {'max_time_out_of_sync': 30, 'name': 'modified-name',
         'hourly_snap_replication_policy':
             replication_session.UnitySnapReplicationPolicy.to_embedded(
                 is_replicating_snaps=True, is_retention_same_as_source=False,
                 is_auto_delete=False, retention_duration=3600),
         'daily_snap_replication_policy':
             replication_session.UnitySnapReplicationPolicy.to_embedded(
                 is_replicating_snaps=False),
         'src_spa_interface': 'FNM00152000052:if_7',
         'src_spb_interface': 'FNM00152000052:if_6',
         'dst_spa_interface': 'FNM00150600267:if_10',
         'dst_spb_interface': 'FNM00150600267:if_11'},
        {'max_time_out_of_sync': 30, 'name': None,
         'hourly_snap_replication_policy': None,
         'daily_snap_replication_policy': None,
         'src_spa_interface': None, 'src_spb_interface': None,
         'dst_spa_interface': None, 'dst_spb_interface': None})
    @ddt.unpack
    def test_modify(self, max_time_out_of_sync, name,
                    hourly_snap_replication_policy,
                    daily_snap_replication_policy,
                    src_spa_interface, src_spb_interface,
                    dst_spa_interface, dst_spb_interface):

        if src_spa_interface:
            src_spa_interface = remote_interface.UnityRemoteInterface(
                _id=src_spa_interface, cli=mock.t_rest())
        if src_spb_interface:
            src_spb_interface = remote_interface.UnityRemoteInterface(
                _id=src_spb_interface, cli=mock.t_rest())
        if dst_spa_interface:
            dst_spa_interface = remote_interface.UnityRemoteInterface(
                _id=dst_spa_interface, cli=mock.t_rest())
        if dst_spb_interface:
            dst_spb_interface = remote_interface.UnityRemoteInterface(
                _id=dst_spb_interface, cli=mock.t_rest())

        rs = replication_session.UnityReplicationSession.get(
            cli=mock.t_rest(),
            _id='42949675780_FNM00150600267_0000'
                '_42949678642_FNM00152000052_0000')
        resp = rs.modify(
            max_time_out_of_sync=max_time_out_of_sync, name=name,
            hourly_snap_replication_policy=hourly_snap_replication_policy,
            daily_snap_replication_policy=daily_snap_replication_policy,
            src_spa_interface=src_spa_interface,
            src_spb_interface=src_spb_interface,
            dst_spa_interface=dst_spa_interface,
            dst_spb_interface=dst_spb_interface)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    @ddt.data(
        {'force_full_copy': True,
         'src_spa_interface': 'FNM00152000052:if_7',
         'src_spb_interface': 'FNM00152000052:if_6',
         'dst_spa_interface': 'FNM00150600267:if_10',
         'dst_spb_interface': 'FNM00150600267:if_11'},
        {'force_full_copy': True,
         'src_spa_interface': None,
         'src_spb_interface': None,
         'dst_spa_interface': None,
         'dst_spb_interface': None})
    @ddt.unpack
    def test_resume(self, force_full_copy,
                    src_spa_interface, src_spb_interface,
                    dst_spa_interface, dst_spb_interface):

        if src_spa_interface:
            src_spa_interface = remote_interface.UnityRemoteInterface(
                _id=src_spa_interface, cli=mock.t_rest())
        if src_spb_interface:
            src_spb_interface = remote_interface.UnityRemoteInterface(
                _id=src_spb_interface, cli=mock.t_rest())
        if dst_spa_interface:
            dst_spa_interface = remote_interface.UnityRemoteInterface(
                _id=dst_spa_interface, cli=mock.t_rest())
        if dst_spb_interface:
            dst_spb_interface = remote_interface.UnityRemoteInterface(
                _id=dst_spb_interface, cli=mock.t_rest())
        rs = replication_session.UnityReplicationSession.get(
            cli=mock.t_rest(),
            _id='42949675780_FNM00150600267_0000'
                '_42949678642_FNM00152000052_0000')
        resp = rs.resume(
            force_full_copy=force_full_copy,
            src_spa_interface=src_spa_interface,
            src_spb_interface=src_spb_interface,
            dst_spa_interface=dst_spa_interface,
            dst_spb_interface=dst_spb_interface)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    def test_pause(self):
        rs = replication_session.UnityReplicationSession.get(
            cli=mock.t_rest(),
            _id='42949675780_FNM00150600267_0000'
                '_42949678642_FNM00152000052_0000')
        resp = rs.pause()
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    def test_sync(self):
        rs = replication_session.UnityReplicationSession.get(
            cli=mock.t_rest(),
            _id='42949675780_FNM00150600267_0000'
                '_42949678642_FNM00152000052_0000')
        resp = rs.sync()
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    @ddt.data({'sync': True, 'force': False},
              {'sync': False, 'force': None})
    @ddt.unpack
    def test_failover(self, sync, force):
        rs = replication_session.UnityReplicationSession.get(
            cli=mock.t_rest(),
            _id='42949675780_FNM00150600267_0000'
                '_42949678642_FNM00152000052_0000')
        resp = rs.failover(sync=sync, force=force)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    @ddt.data({'force_full_copy': True},
              {'force_full_copy': None})
    @ddt.unpack
    def test_failback(self, force_full_copy):
        rs = replication_session.UnityReplicationSession.get(
            cli=mock.t_rest(),
            _id='42949675780_FNM00150600267_0000'
                '_42949678642_FNM00152000052_0000')
        resp = rs.failback(force_full_copy=force_full_copy)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))
