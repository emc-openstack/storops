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

from hamcrest import assert_that, equal_to, contains_string, has_item, \
    only_contains, raises, instance_of, none, is_not, not_none, close_to

from storops.exception import VNXCompressionError, \
    VNXDedupError, VNXLunNotFoundError, \
    VNXLunExtendError, VNXLunExpandSizeError, VNXLunPreparingError, \
    VNXSnapNameInUseError, VNXCompressionAlreadyEnabledError, \
    VNXLunNameInUseError, VNXTargetNotReadyError, \
    VNXCreateSnapResourceNotFoundError, VNXLunInStorageGroupError, \
    VNXAttachSnapLunTypeError, VNXLunInConsistencyGroupError, \
    VNXDetachSnapLunTypeError, VNXDedupAlreadyEnabled, \
    EnumValueNotFoundError, VNXLunHasSnapMountPointError, \
    VNXLunUsedByFeatureError, VNXNameInUseError
from storops.lib.common import instance_cache, cache
from storops.vnx.enums import VNXProvisionEnum, VNXTieringEnum, \
    VNXCompressionRate, VNXSPEnum
from storops.vnx.resource.lun import VNXLun, VNXLunList
from storops.vnx.resource.snap import VNXSnap
from test.vnx.cli_mock import t_cli, patch_cli
from test.vnx.resource.verifiers import verify_lun_0

__author__ = 'Cedric Zhuang'


@patch_cli
@cache
def get_lun_list():
    lun_list = VNXLunList(t_cli())
    return lun_list.update()


class VNXLunTest(TestCase):
    @staticmethod
    def get_lun():
        return VNXLun(lun_id=2, cli=t_cli())

    @patch_cli
    def test_lun_properties(self):
        wwn = '60:06:01:60:12:60:3D:00:95:63:38:87:9D:69:E5:11'
        l = VNXLun(lun_id=3, cli=t_cli())
        assert_that(l.state, equal_to('Ready'))
        assert_that(l.wwn, equal_to(wwn))
        assert_that(l.status, equal_to('OK(0x0)'))
        assert_that(l.operation, equal_to('None'))
        assert_that(l.total_capacity_gb, equal_to(500.0))
        assert_that(l.current_owner, equal_to(VNXSPEnum.SP_A))
        assert_that(l.default_owner, equal_to(VNXSPEnum.SP_A))
        assert_that(l.attached_snapshot, none())
        assert_that(l.lun_id, equal_to(3))
        assert_that(l.name, equal_to('File_CS0_21132_0_d7'))
        assert_that(l.pool_name, equal_to('Pool4File'))
        assert_that(l.is_thin_lun, equal_to(True))
        assert_that(l.is_compressed, equal_to(False))
        assert_that(l.is_dedup, equal_to(False))
        assert_that(l.initial_tier, equal_to('Optimize Pool'))
        assert_that(l.tiering_policy, none())
        assert_that(l.is_private, equal_to(False))
        assert_that(l.user_capacity_gbs, equal_to(500.0))
        assert_that(l.consumed_capacity_gbs, equal_to(512.249))
        assert_that(len(l.snapshot_mount_points), equal_to(0))
        assert_that(l.primary_lun, none())

    @patch_cli
    def test_lun_perf_counters(self):
        l = VNXLun(lun_id=3, cli=t_cli())
        assert_that(l.read_requests, equal_to(1))
        assert_that(l.read_requests_sp_a, equal_to(2))
        assert_that(l.read_requests_sp_b, equal_to(3))
        assert_that(l.write_requests, equal_to(4))
        assert_that(l.write_requests_sp_a, equal_to(5))
        assert_that(l.write_requests_sp_b, equal_to(6))
        assert_that(l.blocks_read, equal_to(7))
        assert_that(l.blocks_read_sp_a, equal_to(8))
        assert_that(l.blocks_read_sp_b, equal_to(9))
        assert_that(l.blocks_written, equal_to(10))
        assert_that(l.blocks_written_sp_a, equal_to(11))
        assert_that(l.blocks_written_sp_b, equal_to(12))
        assert_that(l.busy_ticks, equal_to(13))
        assert_that(l.busy_ticks_sp_a, equal_to(14))
        assert_that(l.busy_ticks_sp_b, equal_to(15))
        assert_that(l.idle_ticks, equal_to(16))
        assert_that(l.idle_ticks_sp_a, equal_to(17))
        assert_that(l.idle_ticks_sp_b, equal_to(18))
        assert_that(l.sum_of_outstanding_requests, equal_to(19))
        assert_that(l.sum_of_outstanding_requests_sp_a, equal_to(20))
        assert_that(l.sum_of_outstanding_requests_sp_b, equal_to(21))
        assert_that(l.non_zero_request_count_arrivals, equal_to(22))
        assert_that(l.non_zero_request_count_arrivals_sp_a, equal_to(23))
        assert_that(l.non_zero_request_count_arrivals_sp_b, equal_to(24))
        assert_that(l.implicit_trespasses, equal_to(25))
        assert_that(l.implicit_trespasses_sp_a, equal_to(26))
        assert_that(l.implicit_trespasses_sp_b, equal_to(27))
        assert_that(l.explicit_trespasses, equal_to(28))
        assert_that(l.explicit_trespasses_sp_a, equal_to(29))
        assert_that(l.explicit_trespasses_sp_b, equal_to(30))
        assert_that(l.extreme_performance, equal_to(1.96))
        assert_that(l.performance, equal_to(5.68))
        assert_that(l.capacity, equal_to(92.37))

    @patch_cli
    def test_lun_state_properties(self):
        lun = VNXLun(lun_id=7, cli=t_cli())
        assert_that(lun.deduplication_state, equal_to('Off'))
        assert_that(lun.deduplication_status, equal_to('OK(0x0)'))
        assert_that(lun.is_dedup, equal_to(False))

    @patch_cli
    def test_lun_status(self):
        lun = self.get_lun()
        assert_that(lun.status, equal_to('OK(0x0)'))
        wwn = '60:06:01:60:1A:50:35:00:6D:29:F1:FC:85:78:E5:11'
        assert_that(lun.wwn, equal_to(wwn))

    @patch_cli
    def test_lun_id_setter_str_input(self):
        lun = self.get_lun()
        assert_that(lun.lun_id, equal_to(2))

    @patch_cli
    def test_lun_provision_default(self):
        lun = VNXLun(lun_id=3, cli=t_cli())
        assert_that(lun.provision, equal_to(VNXProvisionEnum.THIN))

    @patch_cli
    def test_lun_provision_thin(self):
        lun = VNXLun(lun_id=3, cli=t_cli())
        assert_that(lun.provision, equal_to(VNXProvisionEnum.THIN))

    @patch_cli
    def test_lun_provision_compressed(self):
        lun = VNXLun(lun_id=1, cli=t_cli())
        assert_that(lun.provision, equal_to(VNXProvisionEnum.COMPRESSED))

    @patch_cli
    def test_lun_provision_dedup(self):
        lun = VNXLun(lun_id=4, cli=t_cli())
        assert_that(lun.provision, equal_to(VNXProvisionEnum.DEDUPED))

    def test_lun_provision_str_not_valid(self):
        def f():
            lun = VNXLun()
            # noinspection PyPropertyAccess
            lun.provision = 'invalid'

        assert_that(f, raises(AttributeError))

    @patch_cli
    def test_lun_tier_default(self):
        lun = VNXLun(lun_id=5, cli=t_cli())
        assert_that(lun.tier, equal_to(VNXTieringEnum.HIGH_AUTO))

    def test_lun_tier_invalid_str(self):
        def f():
            lun = VNXLun()
            lun.tier = 'invalid'

        assert_that(f, raises(EnumValueNotFoundError))

    def test_lun_tier_highest_available(self):
        lun = VNXLun()
        lun.tiering_policy = 'Auto Tier'
        lun.initial_tier = 'Highest Available'
        assert_that(lun.tier, equal_to(VNXTieringEnum.HIGH_AUTO))

    def test_lun_tier_auto(self):
        lun = VNXLun()
        lun.tiering_policy = 'Auto Tier'
        lun.initial_tier = 'Optimize Pool'
        assert_that(lun.tier, equal_to(VNXTieringEnum.AUTO))

    def test_lun_tier_high(self):
        lun = VNXLun()
        lun.tiering_policy = 'Highest Available'
        lun.initial_tier = 'Highest Available'
        assert_that(lun.tier, equal_to(VNXTieringEnum.HIGH))

    def test_lun_tier_low(self):
        lun = VNXLun()
        lun.tiering_policy = 'Lowest Available'
        lun.initial_tier = 'Lowest Available'
        assert_that(lun.tier, equal_to(VNXTieringEnum.LOW))

    def test_lun_tier_no_move_high_tier(self):
        lun = VNXLun()
        lun.tiering_policy = 'No Movement'
        lun.initial_tier = 'Highest Available'
        assert_that(lun.tier, equal_to(VNXTieringEnum.NO_MOVE))

    def test_lun_tier_no_move_optimize_pool(self):
        lun = VNXLun()
        lun.tiering_policy = 'No Movement'
        lun.initial_tier = 'Optimize Pool'
        assert_that(lun.tier, equal_to(VNXTieringEnum.NO_MOVE))

    @patch_cli
    def test_update(self):
        lun = self.get_lun()
        assert_that(lun.total_capacity_gb, equal_to(2.0))
        assert_that(lun.provision, equal_to(VNXProvisionEnum.THIN))
        assert_that(lun.tier, equal_to(VNXTieringEnum.HIGH_AUTO))

    @patch_cli
    def test_repr(self):
        lun = self.get_lun()
        assert_that(str(lun), contains_string('"VNXLun": {'))
        assert_that(str(lun), contains_string(
            '"current_owner": "VNXSPEnum.SP_A"'))

    @patch_cli
    def test_get_snap(self):
        lun = VNXLun(lun_id=3, cli=t_cli())
        snaps = lun.get_snap()
        assert_that(len(snaps), equal_to(2))
        for snap in snaps:
            assert_that(snap.source_luns, has_item(lun.get_id(lun)))

    @patch_cli
    def test_get_lun_by_id(self):
        lun = VNXLun(lun_id=0, cli=t_cli())
        lun.update()
        verify_lun_0(lun)

    @patch_cli
    def test_get_lun_by_name(self):
        lun = VNXLun(name='x', cli=t_cli())
        lun.update()
        verify_lun_0(lun)

    @patch_cli
    def test_create_success(self):
        lun = VNXLun.create(t_cli(),
                            pool_id=0,
                            lun_id=2,
                            size_gb=2)
        assert_that(lun.user_capacity_gbs, equal_to(2.0))

    @patch_cli
    def test_create_name_in_use(self):
        def f():
            VNXLun.create(t_cli(), pool_id=0, lun_id=3)

        assert_that(f, raises(VNXLunNameInUseError, 'already in use'))

    def test_get_lun_id_str(self):
        assert_that(VNXLun.get_id('123'), equal_to(123))

    def test_get_lun_obj_member(self):
        lun = VNXLun(lun_id=12)
        assert_that(VNXLun.get_id(lun), equal_to(12))

    @patch_cli
    def test_get_lun_obj_property(self):
        lun = VNXLun(name='x', cli=t_cli())
        assert_that(VNXLun.get_id(lun), equal_to(0))

    def test_get_lun_id_int(self):
        assert_that(VNXLun.get_id(23), equal_to(23))

    def test_get_lun_id_err(self):
        def f():
            VNXLun.get_id('abc')

        assert_that(f, raises(ValueError, 'invalid lun number'))

    @patch_cli
    def test_get_migration_session(self):
        lun = VNXLun(lun_id=0, cli=t_cli())
        ms = lun.get_migration_session()
        assert_that(ms.existed, equal_to(True))

    @patch_cli
    def test_primary_lun_none(self):
        lun = self.get_lun()
        assert_that(lun.primary_lun, none())

    @patch_cli
    def test_attached_snapshot_none(self):
        lun = self.get_lun()
        assert_that(lun.attached_snapshot, none())

    @patch_cli
    def test_attached_snapshot_invalid_lun_type(self):
        def f():
            lun = VNXLun(name='l1', cli=t_cli())
            lun.attach_snap('s1')

        assert_that(f, raises(VNXAttachSnapLunTypeError, 'Invalid LUN type.'))

    @patch_cli
    def test_detach_snap_invalid_lun_type(self):
        def f():
            lun = VNXLun(lun_id=0, cli=t_cli())
            lun.detach_snap()

        assert_that(f, raises(VNXDetachSnapLunTypeError,
                              'not a snapshot mount point'))

    @patch_cli
    def test_create_mount_point_success(self):
        lun = VNXLun(name='l1', cli=t_cli())
        m2 = lun.create_mount_point(name='m2')
        assert_that(lun.snapshot_mount_points, instance_of(VNXLunList))
        assert_that(str(lun), contains_string('"VNXLunList": ['))
        for smp in lun.snapshot_mount_points:
            assert_that(smp, instance_of(VNXLun))
            pl = smp.primary_lun
            assert_that(pl, instance_of(VNXLun))
            assert_that(pl._get_name(), equal_to('l1'))
        assert_that(m2.attached_snapshot, none())

    @patch_cli
    def test_mount_point_properties(self):
        lun = VNXLun(name='l1', cli=t_cli())
        m1 = lun.create_mount_point(name='m1')
        assert_that(m1.name, equal_to('m1'))
        assert_that(m1.lun_id, equal_to(4057))
        s1 = m1.attached_snapshot
        assert_that(s1, instance_of(VNXSnap))
        assert_that(s1._cli, equal_to(t_cli()))
        assert_that(s1._get_name(), equal_to('s1'))

    @patch_cli
    def test_create_mount_point_name_in_use(self):
        def f():
            lun = VNXLun(name='l1', cli=t_cli())
            lun.create_mount_point(name='m3')

        assert_that(f, raises(VNXLunNameInUseError, 'already in use'))

    @patch_cli
    def test_attach_snap(self):
        m1 = VNXLun(name='m1', cli=t_cli())
        s1 = VNXSnap(name='s1', cli=t_cli())
        m1.attach_snap(s1)
        m1.update()
        assert_that(m1.attached_snapshot._get_name(), equal_to('s1'))

    @patch_cli
    def test_property_instance_cache(self):
        m1 = VNXLun(name='m1', cli=t_cli())
        s1 = m1.attached_snapshot
        s2 = m1.attached_snapshot
        assert_that(hash(s1), equal_to(hash(s2)))
        m1.update()
        s3 = m1.attached_snapshot
        assert_that(hash(s3), is_not(equal_to(hash(s1))))
        assert_that(s1._cli, not_none())

    @patch_cli
    def test_change_name(self):
        l = VNXLun(name='m1', cli=t_cli())
        l.name = 'l1'
        assert_that(l.name, equal_to('l1'))

    @patch_cli
    def test_change_name_not_found(self):
        def f():
            l = VNXLun(lun_id=4000, cli=t_cli())
            l.name = 'l1'

        assert_that(f, raises(VNXLunNotFoundError, 'may not exist'))

    @patch_cli
    def test_change_name_failed(self):
        l = VNXLun(name='l1', cli=t_cli())
        try:
            l.name = 'l3'
            self.fail('should have raised an exception.')
        except VNXNameInUseError:
            assert_that(l._get_name(), equal_to('l1'))

    @patch_cli
    def test_change_tier(self):
        def f():
            l = VNXLun(lun_id=4000, cli=t_cli())
            l.tier = VNXTieringEnum.LOW

        assert_that(f, raises(VNXLunNotFoundError, 'may not exist'))

    @patch_cli
    def test_expand_too_large(self):
        def f():
            l = VNXLun(lun_id=0, cli=t_cli())
            l.expand(999999)

        assert_that(f, raises(VNXLunExtendError,
                              'capacity specified is not supported'))

    @patch_cli
    def test_expand_file_lun(self):
        def f():
            l = VNXLun(lun_id=1, cli=t_cli())
            l.expand(500)

        assert_that(f, raises(VNXLunExtendError,
                              'affect a File System Storage'))

    @patch_cli
    def test_expand_too_small(self):
        def f():
            l = VNXLun(lun_id=1, cli=t_cli())
            l.expand(1)

        assert_that(f, raises(VNXLunExpandSizeError,
                              'greater than current LUN size'))

    @patch_cli
    def test_expand_preparing(self):
        def f():
            l = VNXLun(lun_id=1, cli=t_cli())
            l.expand(12)

        assert_that(f, raises(VNXLunPreparingError,
                              "is 'Preparing"))

    def test_get_id(self):
        l1 = VNXLun(lun_id=11)
        assert_that(VNXLun.get_id(l1), equal_to(11))

    @patch_cli
    def test_get_id_with_update(self):
        m1 = VNXLun(name='m1', cli=t_cli())
        assert_that(VNXLun.get_id(m1), equal_to(4057))

    def test_get_id_list(self):
        l22 = VNXLun(lun_id=22)
        l23 = VNXLun(lun_id=23)
        assert_that(VNXLun.get_id_list(l22, l23), only_contains(22, 23))

    @patch_cli
    def test_enable_compression_failed(self):
        def method():
            l1 = VNXLun(lun_id=19, cli=t_cli())
            l1.enable_compression(VNXCompressionRate.HIGH)

        def prop():
            l1 = VNXLun(lun_id=19, cli=t_cli())
            l1.is_compressed = True

        assert_that(method, raises(VNXCompressionAlreadyEnabledError,
                                   'already turned on'))
        assert_that(prop, raises(VNXCompressionError, 'not installed'))

    @patch_cli
    def test_enable_compression_ignore_threshold(self):
        def f():
            l1 = VNXLun(lun_id=3, cli=t_cli())
            l1.enable_compression(VNXCompressionRate.LOW, True)

        assert_that(f, raises(VNXCompressionAlreadyEnabledError,
                              'already turned on'))

    @patch_cli
    def test_disable_compression(self):
        def method():
            l1 = VNXLun(lun_id=19, cli=t_cli())
            l1.disable_compression()

        def prop():
            l1 = VNXLun(lun_id=19, cli=t_cli())
            l1.is_compressed = False

        assert_that(method, raises(VNXCompressionError, 'not turned on'))
        assert_that(prop, raises(VNXCompressionError, 'not turned on'))

    @patch_cli
    def test_enable_dedup(self):
        def method_call():
            l1 = VNXLun(name='l1', cli=t_cli())
            l1.enable_dedup()

        def set_property():
            l1 = VNXLun(name='l1', cli=t_cli())
            l1.is_dedup = True

        assert_that(method_call, raises(VNXDedupError, 'it is migrating'))
        assert_that(set_property, raises(VNXDedupError, 'it is migrating'))

    @patch_cli
    def test_dedup_already_enabled(self):
        def f():
            l2 = VNXLun(name='l2', cli=t_cli())
            l2.enable_dedup()

        assert_that(f, raises(VNXDedupAlreadyEnabled, 'already enabled'))

    @patch_cli
    def test_dedup_enabling(self):
        def f():
            l2 = VNXLun(name='l3', cli=t_cli())
            l2.enable_dedup()

        assert_that(f, raises(VNXDedupAlreadyEnabled, 'or enabling'))

    @patch_cli
    def test_disable_dedup(self):
        def method_call():
            l1 = VNXLun(name='l1', cli=t_cli())
            l1.disable_dedup()

        def set_property():
            l1 = VNXLun(name='l1', cli=t_cli())
            l1.is_dedup = False

        assert_that(method_call, raises(VNXDedupError, 'disabled or'))
        assert_that(set_property, raises(VNXDedupError, 'disabled or'))

    @patch_cli
    def test_delete_lun_not_exists(self):
        def f():
            l1 = VNXLun(name='not_exists', cli=t_cli())
            l1.delete()

        assert_that(f, raises(VNXLunNotFoundError, 'not exist'))

    @patch_cli
    def test_delete_lun_in_storage_group(self):
        def f():
            l2 = VNXLun(name='in_sg', cli=t_cli())
            l2.delete()

        assert_that(f, raises(VNXLunInStorageGroupError, 'in a Storage Group'))

    @patch_cli
    def test_delete_lun_in_cg(self):
        def f():
            l2 = VNXLun(name='l2', cli=t_cli())
            l2.delete()

        assert_that(f, raises(VNXLunInConsistencyGroupError,
                              'member of a consistency group'))

    @patch_cli
    def test_delete_lun_has_smp_not_force(self):
        def f():
            l2 = VNXLun(name='has_smp', cli=t_cli())
            l2.delete()

        assert_that(f, raises(VNXLunHasSnapMountPointError,
                              'has snapshot mount points'))

    @patch_cli
    def test_delete_lun_has_smp_force(self):
        l = VNXLun(lun_id=196, cli=t_cli())
        # no error raised
        l.delete(force=True)

    @patch_cli
    def test_delete_lun_has_migration(self):
        def f():
            l = VNXLun(name='lun_in_migration', cli=t_cli())
            l.delete()

        assert_that(f, raises(VNXLunUsedByFeatureError,
                              'Cannot unbind LUN'))

    @patch_cli
    def test_create_snap(self):
        def f():
            l1 = VNXLun(lun_id=11, cli=t_cli())
            l1.create_snap('s1')

        assert_that(f, raises(VNXCreateSnapResourceNotFoundError,
                              'Cannot create the snapshot'))

    @patch_cli
    def test_create_snap_existed(self):
        def f():
            l1 = VNXLun(lun_id=3, cli=t_cli())
            l1.create_snap('s1')

        assert_that(f, raises(VNXSnapNameInUseError,
                              'already in use'))

    @patch_cli
    def test_migration_dst_lun_not_available(self):
        def f():
            l1 = VNXLun(lun_id=1, cli=t_cli())
            l2 = VNXLun(lun_id=2, cli=t_cli())
            l1.migrate(l2)

        assert_that(f, raises(VNXTargetNotReadyError,
                              'not available for migration'))

    @patch_cli
    def test_create_mirror_view(self):
        l = VNXLun(lun_id=245, cli=t_cli())
        mv = l.create_mirror_view('mv0')
        assert_that(mv.state, equal_to('Active'))

    @patch_cli
    def test_get_source_mirror_view(self):
        l = self.get_lun()
        assert_that(len(l.get_mirror_view(as_src=True)), equal_to(1))

    @patch_cli
    def test_get_target_mirror_view(self):
        l = self.get_lun()
        assert_that(len(l.get_mirror_view(as_tgt=True)), equal_to(2))

    @patch_cli
    def test_get_mirror_view_all(self):
        l = self.get_lun()
        assert_that(len(l.get_mirror_view(as_src=True, as_tgt=True)),
                    equal_to(3))
        assert_that(len(l.get_mirror_view()), equal_to(3))

    @patch_cli
    def test_force_delete_lun_not_found(self):
        def f():
            lun = VNXLun(name='y', cli=t_cli())
            lun.delete(force=True)

        assert_that(f, raises(VNXLunNotFoundError, 'may not exist'))

    @property
    @instance_cache
    def lun_5(self):
        return VNXLun(lun_id=5, cli=t_cli())

    @patch_cli
    def test_lun_read_iops(self):
        assert_that(self.lun_5.read_iops, equal_to(2.0))

    @patch_cli
    def test_lun_read_iops_spa(self):
        assert_that(self.lun_5.read_iops_sp_a, equal_to(1.5))

    @patch_cli
    def test_lun_read_iops_spb(self):
        assert_that(self.lun_5.read_iops_sp_b, equal_to(0.5))

    @patch_cli
    def test_lun_write_iops(self):
        assert_that(self.lun_5.write_iops, equal_to(4.0))

    @patch_cli
    def test_lun_write_iops_spa(self):
        assert_that(self.lun_5.write_iops_sp_a, equal_to(3.0))

    @patch_cli
    def test_lun_write_iops_spb(self):
        assert_that(self.lun_5.write_iops_sp_b, equal_to(1.0))

    @patch_cli
    def test_lun_total_iops(self):
        assert_that(self.lun_5.total_iops, equal_to(6.0))

    @patch_cli
    def test_lun_read_mbps(self):
        assert_that(self.lun_5.read_mbps, equal_to(2.3))

    @patch_cli
    def test_lun_read_mbps_spa(self):
        assert_that(self.lun_5.read_mbps_sp_a, equal_to(1.1))

    @patch_cli
    def test_lun_read_mbps_spb(self):
        assert_that(self.lun_5.read_mbps_sp_b, equal_to(1.2))

    @patch_cli
    def test_lun_write_mbps(self):
        assert_that(self.lun_5.write_mbps, equal_to(2.7))

    @patch_cli
    def test_lun_write_mbps_spa(self):
        assert_that(self.lun_5.write_mbps_sp_a, equal_to(1.3))

    @patch_cli
    def test_lun_write_mbps_spb(self):
        assert_that(self.lun_5.write_mbps_sp_b, equal_to(1.4))

    @patch_cli
    def test_lun_total_mbps(self):
        assert_that(self.lun_5.total_mbps, equal_to(5.0))

    @patch_cli
    def test_lun_read_size_kb(self):
        assert_that(self.lun_5.read_size_kb, equal_to(1177.6))

    @patch_cli
    def test_lun_write_size_kb(self):
        assert_that(self.lun_5.write_size_kb, equal_to(691.2))

    @patch_cli
    def test_lun_utilization(self):
        assert_that(self.lun_5.utilization, close_to(33.33, 0.01))

    @patch_cli
    def test_lun_utilization_spa(self):
        assert_that(self.lun_5.utilization_sp_a, close_to(44.44, 0.01))

    @patch_cli
    def test_lun_utilization_spb(self):
        assert_that(self.lun_5.utilization_sp_b, close_to(16.66, 0.01))

    @patch_cli
    def test_lun_implicit_trespasses_ps(self):
        assert_that(self.lun_5.implicit_trespasses_ps, equal_to(3.0))

    @patch_cli
    def test_lun_implicit_trespasses_ps_sp_a(self):
        assert_that(self.lun_5.implicit_trespasses_ps_sp_a, equal_to(1.0))

    @patch_cli
    def test_lun_implicit_trespasses_ps_sp_b(self):
        assert_that(self.lun_5.implicit_trespasses_ps_sp_b, equal_to(2.0))

    @patch_cli
    def test_lun_explicit_trespasses_ps(self):
        assert_that(self.lun_5.explicit_trespasses_ps, equal_to(7.0))

    @patch_cli
    def test_lun_explicit_trespasses_ps_sp_a(self):
        assert_that(self.lun_5.explicit_trespasses_ps_sp_a, equal_to(3.0))

    @patch_cli
    def test_lun_explicit_trespasses_ps_sp_b(self):
        assert_that(self.lun_5.explicit_trespasses_ps_sp_b, equal_to(4.0))


class VNXLunMigrationCallbackTest(TestCase):
    @patch_cli
    def test_migration_on_complete_session_not_found(self):
        c = _Counter()

        def on_complete():
            c.increase()

        l0 = VNXLun(name='lun0', cli=t_cli())
        l1 = VNXLun(name='lun1', cli=t_cli())
        l0.migrate(l1, on_complete=on_complete).join()
        assert_that(c.x, equal_to(1))

    @patch_cli
    def test_migration_on_error(self):
        c = _Counter()

        def on_error():
            c.decrease()

        l0 = VNXLun(name='lun0', cli=t_cli())
        l2 = VNXLun(name='lun2', cli=t_cli())
        l2.migrate(l0, on_error=on_error).join()
        assert_that(c.x, equal_to(-1))


class _Counter(object):
    def __init__(self):
        self.x = 0

    def increase(self):
        self.x += 1

    def decrease(self):
        self.x -= 1


class VNXLunListTest(TestCase):
    lun_list = get_lun_list()

    @patch_cli
    def test_get_lun_list(self):
        assert_that(self.lun_list, instance_of(VNXLunList))
        assert_that(len(self.lun_list), equal_to(183))

    @patch_cli
    def test_get_lun_by_id_found(self):
        lun = self.lun_list.get(148)
        assert_that(lun.lun_id, equal_to(148))

    @patch_cli
    def test_get_lun_by_lun(self):
        lun = self.lun_list.get(VNXLun(lun_id=148, cli=t_cli()))
        assert_that(lun.lun_id, equal_to(148))

    @patch_cli
    def test_get_lun_by_id_not_found(self):
        lun = self.lun_list.get(12345)
        assert_that(lun, none())

    @patch_cli
    def test_lun_list_perf_properties(self):
        read_iops_values = set(self.lun_list.read_iops)
        assert_that(read_iops_values, has_item(2.0))

    @patch_cli
    def test_shadow_copy(self):
        ret = self.lun_list.shadow_copy(lun_ids=[186, 151, 79])
        assert_that(len(ret), equal_to(3))
        # verify the original list is not touched
        assert_that(len(self.lun_list), equal_to(183))
        assert_that(ret.timestamp, equal_to(self.lun_list.timestamp))
