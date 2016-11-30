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

from unittest import TestCase

from hamcrest import assert_that, only_contains, instance_of, \
    contains_string, raises, none, has_item, is_not
from hamcrest import equal_to

from storops import UnitySystem
from storops.exception import UnitySnapNameInUseError, \
    UnityLunNameInUseError, UnityLunShrinkNotSupportedError, \
    UnityNothingToModifyError, UnityPerfMonNotEnabledError
from storops.unity.enums import HostLUNAccessEnum, NodeEnum
from storops.unity.resource.disk import UnityDisk
from storops.unity.resource.host import UnityBlockHostAccessList, UnityHost
from storops.unity.resource.lun import UnityLun, UnityLunList
from storops.unity.resource.pool import UnityPool
from storops.unity.resource.port import UnityIoLimitPolicy, \
    UnityIoLimitRuleSetting
from storops.unity.resource.snap import UnitySnap
from storops.unity.resource.sp import UnityStorageProcessor
from storops.unity.resource.storage_resource import UnityStorageResource
from test.unity.rest_mock import t_rest, patch_rest, t_unity
from test.utils import is_nan

__author__ = 'Cedric Zhuang'


class UnityLunTest(TestCase):
    @patch_rest
    def test_get_lun_sv2_simple_property(self):
        lun = UnityLun(_id='sv_2', cli=t_rest())
        assert_that(lun.existed, equal_to(True))
        assert_that(lun.id, equal_to('sv_2'))
        assert_that(lun.name, equal_to('openstack_lun'))
        assert_that(lun.description, equal_to('sample'))
        assert_that(lun.size_total, equal_to(107374182400))
        assert_that(lun.total_size_gb, equal_to(100))
        assert_that(lun.size_allocated, equal_to(0))
        assert_that(lun.per_tier_size_used, only_contains(2952790016, 0, 0))
        assert_that(lun.is_thin_enabled, equal_to(True))
        assert_that(lun.wwn, equal_to(
            '60:06:01:60:17:50:3C:00:C2:0A:D5:56:92:D1:BA:12'))
        assert_that(lun.is_replication_destination, equal_to(False))
        assert_that(lun.is_snap_schedule_paused, equal_to(False))
        assert_that(lun.metadata_size, equal_to(5100273664))
        assert_that(lun.metadata_size_allocated, equal_to(2684354560))
        assert_that(lun.snap_wwn, equal_to(
            '60:06:01:60:17:50:3C:00:C4:0A:D5:56:00:95:DE:11'))
        assert_that(lun.snaps_size, equal_to(0))
        assert_that(lun.snaps_size_allocated, equal_to(0))
        assert_that(lun.snap_count, equal_to(0))
        assert_that(lun.storage_resource, instance_of(UnityStorageResource))
        assert_that(lun.pool, instance_of(UnityPool))
        assert_that(lun.io_limit_rule, none())

    @patch_rest
    def test_lun_modify_host_access(self):
        host = UnityHost(_id="Host_1", cli=t_rest())
        lun = UnityLun(_id='sv_4', cli=t_rest())
        host_access = [{'host': host, 'accessMask': HostLUNAccessEnum.BOTH}]
        lun.modify(host_access=host_access)
        lun.update()
        assert_that(lun.host_access[0].host, equal_to(host))
        assert_that(lun.host_access[0].access_mask,
                    equal_to(HostLUNAccessEnum.BOTH))

    @patch_rest
    def test_lun_modify_sp(self):
        lun = UnityLun(_id='sv_4', cli=t_rest())
        sp = UnityStorageProcessor(_id='spb', cli=t_rest())
        lun.modify(sp=sp)
        lun.update()
        assert_that(sp.to_node_enum(), equal_to(NodeEnum.SPB))

    @patch_rest
    def test_lun_modify_none(self):
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.modify(host_access=None)
        lun.update()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_lun_modify_wipe_host_access(self):
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.modify(host_access=[])
        lun.update()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_lun_modify_muitl_property_except_sp(self):
        lun = UnityLun(_id='sv_4', cli=t_rest())
        lun.modify(name="RestLun100", is_thin=True,
                   description="Lun description")
        lun.update()
        assert_that(lun.name, equal_to('RestLun100'))
        assert_that(lun.description, equal_to('Lun description'))

    @patch_rest
    def test_lun_delete(self):
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.delete(force_snap_delete=True, force_vvol_delete=True)
        lun.update()
        assert_that(resp.is_ok(), equal_to(True))
        assert_that(resp.job.existed, equal_to(False))

    @patch_rest
    def test_lun_attach_to_new_host(self):
        host = UnityHost(_id="Host_10", cli=t_rest())
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.attach_to(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_lun_attach_to_same_host(self):
        host = UnityHost(_id="Host_1", cli=t_rest())
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.attach_to(host, access_mask=HostLUNAccessEnum.BOTH)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_lun_detach_from_host(self):
        host = UnityHost(_id="Host_1", cli=t_rest())
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.detach_from(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_get_lun_sv2_nested_property_update_property(self):
        lun = UnityLun(_id='sv_2', cli=t_rest())
        sr = lun.storage_resource
        assert_that(sr._cli, equal_to(t_rest()))
        assert_that(sr.size_total, equal_to(107374182400))

    @patch_rest
    def test_get_lun_sv3_nested_property_no_update(self):
        lun = UnityLunList.get(_id='sv_3', cli=t_rest())
        sr = lun.storage_resource
        assert_that(sr._cli, equal_to(t_rest()))

    @patch_rest
    def test_get_lun_all_0(self):
        lun_list = UnityLunList.get(cli=t_rest())
        assert_that(len(lun_list), equal_to(5))

    @patch_rest
    def test_get_lun_doc(self):
        lun = UnityLun(_id='sv_2', cli=t_rest())
        doc = lun.doc
        assert_that(doc,
                    contains_string('Represents Volume, LUN, Virtual Disk.'))
        assert_that(doc, contains_string('current_node'))
        assert_that(doc, contains_string('Current SP'))

    @patch_rest
    def test_get_lun_with_host_access(self):
        unity = UnitySystem('10.109.22.101', 'admin', 'Password123!')
        lun = unity.get_lun(_id='sv_567')
        assert_that(lun.host_access, instance_of(UnityBlockHostAccessList))
        access = lun.host_access[0]
        assert_that(access.access_mask, equal_to(HostLUNAccessEnum.PRODUCTION))
        assert_that(access.host, instance_of(UnityHost))
        assert_that(access.host.id, equal_to('Host_1'))

    @patch_rest
    def test_lun_snap_create(self):
        lun = UnityLun(_id='sv_8', cli=t_rest())
        snap = lun.create_snap(name='lun_snap_1')
        assert_that(snap, instance_of(UnitySnap))

    @patch_rest
    def test_lun_snapshots(self):
        lun = UnityLun(_id='sv_8', cli=t_rest())
        assert_that(len(lun.snapshots), equal_to(3))

    @patch_rest
    def test_lun_snap_create_existing(self):
        lun = UnityLun(_id='sv_9', cli=t_rest())
        assert_that(lambda: lun.create_snap(name='lun_snap_1'),
                    raises(UnitySnapNameInUseError))

    @patch_rest
    def test_lun_rename(self):
        def f():
            lun = UnityLun(_id='sv_2', cli=t_rest())
            lun.name = 'Europa'

        assert_that(f, raises(UnityLunNameInUseError, 'already exists'))

    @patch_rest
    def test_lun_max_iops_property(self):
        lun = UnityLun(_id='sv_10', cli=t_rest())
        assert_that(lun.max_iops, equal_to(3600))
        assert_that(lun.max_kbps, none())

    @patch_rest
    def test_lun_max_kbps_property(self):
        lun = UnityLun(_id='sv_11', cli=t_rest())
        assert_that(lun.max_iops, none())
        assert_that(lun.max_kbps, equal_to(11000))

    @patch_rest
    def test_create_with_io_limit(self):
        cli = t_rest()
        policy = UnityIoLimitPolicy('qp_4', cli=cli)
        pool = UnityPool('pool_1', cli=cli)
        lun = pool.create_lun('Himalia', io_limit_policy=policy)
        assert_that(lun.name, equal_to('Himalia'))
        assert_that(lun.io_limit_policy.get_id(), equal_to('qp_4'))
        rule = lun.io_limit_rule
        assert_that(rule, instance_of(UnityIoLimitRuleSetting))
        assert_that(rule.max_kbps_density, equal_to(1100))
        assert_that(rule.name, equal_to('Density_1100_KBPS_rule'))

    @patch_rest
    def test_expand_lun_success(self):
        lun = UnityLun('sv_2', cli=t_rest())
        original_size = lun.expand(101 * 1024 ** 3)
        assert_that(original_size / 1024 ** 3, equal_to(100))

    @patch_rest
    def test_expand_lun_too_small(self):
        def f():
            lun = UnityLun('sv_2', cli=t_rest())
            lun.total_size_gb = 1

        assert_that(f, raises(UnityLunShrinkNotSupportedError, 'shrink'))

    @patch_rest
    def test_expand_lun_equal_size(self):
        def f():
            lun = UnityLun('sv_2', cli=t_rest())
            lun.total_size_gb = 100

        assert_that(f, raises(UnityNothingToModifyError, 'nothing to modify'))

    @patch_rest
    def test_lun_read_iops(self):
        lun = t_unity().get_lun(_id='sv_2')
        assert_that(lun.read_iops, equal_to(1.5))

    @patch_rest
    def test_lun_write_iops(self):
        lun = t_unity().get_lun(_id='sv_2')
        assert_that(lun.write_iops, equal_to(3.0))

    @patch_rest
    def test_lun_perf_disabled_exception(self):
        unity = UnitySystem('10.244.223.61', 'a', 'a')
        unity.disable_perf_stats()

        def f():
            return unity.get_lun(_id='sv_2').read_iops

        assert_that(f, raises(UnityPerfMonNotEnabledError, 'not enabled'))


class UnityLunEnablePerfStatsTest(TestCase):
    @patch_rest
    def setUp(self):
        self.unity = UnitySystem('10.244.223.61', 'a', 'a')
        self.unity.enable_perf_stats(1, [UnityDisk])

    @patch_rest
    def tearDown(self):
        self.unity.disable_perf_stats()

    @patch_rest
    def test_lun_perf_not_enabled_exception(self):
        disk = self.unity.get_disk(_id='dae_0_1_disk_0')
        assert_that(disk.read_iops, is_nan())

        def f():
            return self.unity.get_lun(_id='sv_2').read_iops

        assert_that(f, raises(UnityPerfMonNotEnabledError, 'not enabled'))

    @patch_rest
    def test_lun_properties_perf_not_enabled(self):
        lun = self.unity.get_lun(_id='sv_2')
        assert_that(lun.property_names, is_not(has_item('read_iops')))
        disk = self.unity.get_disk(_id='dae_0_1_disk_0')
        assert_that(disk.property_names(), has_item('read_iops'))
