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

from hamcrest import assert_that, equal_to, instance_of, raises

from storops.exception import UnityLunNameInUseError, JobStateError, \
    UnityPoolNameInUseError
from storops.unity.enums import RaidTypeEnum, FastVPStatusEnum, \
    FastVPRelocationRateEnum, PoolDataRelocationTypeEnum, \
    RaidStripeWidthEnum, TierTypeEnum, PoolUnitTypeEnum, \
    FSSupportedProtocolEnum, TieringPolicyEnum, JobStateEnum, \
    StoragePoolTypeEnum
from storops.unity.resource.disk import UnityDiskGroup, UnityDisk
from storops.unity.resource.pool import UnityPool, UnityPoolList, \
    RaidGroupParameter
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.sp import UnityStorageProcessor
from storops.unity.resource.nas_server import UnityNasServer

from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityPoolTest(TestCase):
    @patch_rest
    def test_properties(self):
        pool = UnityPool(_id='pool_1', cli=t_rest())
        self.verify_pool_1(pool)

    @staticmethod
    def verify_pool_1(pool):
        assert_that(pool.id, equal_to('pool_1'))
        assert_that(pool.raid_type, equal_to(RaidTypeEnum.MIXED))
        assert_that(pool.name, equal_to('perfpool1130'))
        assert_that(pool.description, equal_to('pp'))
        assert_that(pool.size_free, equal_to(9160359936000))
        assert_that(pool.size_total, equal_to(9251627991040))
        assert_that(pool.size_used, equal_to(91268055040))
        assert_that(pool.size_subscribed, equal_to(1392106274816))
        assert_that(pool.alert_threshold, equal_to(70))
        assert_that(pool.pool_space_harvest_high_threshold, equal_to(95.0))
        assert_that(pool.pool_space_harvest_low_threshold, equal_to(85.0))
        assert_that(pool.snap_space_harvest_high_threshold, equal_to(25.0))
        assert_that(pool.snap_space_harvest_low_threshold, equal_to(20.0))
        assert_that(pool.is_fast_cache_enabled, equal_to(False))
        assert_that(str(pool.creation_time),
                    equal_to('2016-02-29 07:34:23+00:00'))
        assert_that(pool.is_empty, equal_to(False))
        assert_that(pool.is_harvest_enabled, equal_to(True))
        assert_that(pool.is_snap_harvest_enabled, equal_to(False))
        assert_that(pool.metadata_size_subscribed, equal_to(59324235776))
        assert_that(pool.snap_size_subscribed, equal_to(873220538368))
        assert_that(pool.metadata_size_used, equal_to(36775657472))
        assert_that(pool.snap_size_used, equal_to(24452407296))
        assert_that(pool.is_all_flash, equal_to(False))
        assert_that(pool.pool_type, equal_to(StoragePoolTypeEnum.TRADITIONAL))
        tiers = pool.tiers

        assert_that(len(tiers), equal_to(3))
        for tier in tiers:
            assert_that(tier._cli, equal_to(pool._cli))

        assert_that(pool.pool_fast_vp._cli, equal_to(pool._cli))

    @patch_rest
    def test_pool_fast_vp_properties(self):
        pool = UnityPool(_id='pool_1', cli=t_rest())
        fast = pool.pool_fast_vp
        assert_that(fast.status, equal_to(FastVPStatusEnum.ACTIVE))
        assert_that(fast.relocation_rate,
                    equal_to(FastVPRelocationRateEnum.MEDIUM))
        assert_that(fast.type, equal_to(PoolDataRelocationTypeEnum.SCHEDULED))
        assert_that(fast.is_schedule_enabled, equal_to(True))
        assert_that(str(fast.relocation_duration_estimate),
                    equal_to('0:00:00'))
        assert_that(fast.size_moving_down, equal_to(0))
        assert_that(fast.size_moving_up, equal_to(0))
        assert_that(fast.size_moving_within, equal_to(0))
        assert_that(fast.percent_complete, equal_to(0))
        assert_that(fast.data_relocated, equal_to(0))
        assert_that(str(fast.last_start_time),
                    equal_to('2016-03-13 22:00:00+00:00'))
        assert_that(str(fast.last_end_time),
                    equal_to('2016-03-14 06:00:00+00:00'))

    @patch_rest
    def test_tier_properties(self):
        pool = UnityPool(_id='pool_1', cli=t_rest())
        tier = next(t for t in pool.tiers if t.name == 'Performance')
        assert_that(tier.raid_type, equal_to(RaidTypeEnum.RAID5))
        assert_that(tier.stripe_width, equal_to(RaidStripeWidthEnum._5))
        assert_that(tier.tier_type, equal_to(TierTypeEnum.PERFORMANCE))
        assert_that(tier.size_total, equal_to(1180847570944))
        assert_that(tier.size_used, equal_to(3489660928))
        assert_that(tier.size_free, equal_to(1177357910016))
        assert_that(tier.size_moving_down, equal_to(0))
        assert_that(tier.size_moving_up, equal_to(0))
        assert_that(tier.size_moving_within, equal_to(0))
        assert_that(tier.disk_count, equal_to(5))

    @patch_rest
    def test_get_all(self):
        pools = UnityPoolList(cli=t_rest())
        assert_that(len(pools), equal_to(2))

        pool = next(pool for pool in pools if pool.id == 'pool_1')
        self.verify_pool_1(pool)

    @patch_rest
    def test_disk_groups(self):
        cli = t_rest()
        pool0 = UnityPool.get(cli=cli, _id='pool_1')
        disk_groups = pool0.disk_groups
        assert_that(disk_groups, instance_of(dict))
        assert_that(len(disk_groups), equal_to(2))
        assert_that(disk_groups['dg_8'], instance_of(list))
        assert_that(disk_groups['dg_15'], instance_of(list))
        for key in disk_groups:
            for disk in disk_groups[key]:
                assert_that(disk, instance_of(UnityDisk))

    @patch_rest
    def test_get_nested_resource_properties(self):
        pools = UnityPoolList(cli=t_rest())
        pool = next(pool for pool in pools if pool.id == 'pool_1')
        tier = next(t for t in pool.tiers if t.name == 'Performance')
        unit = next(u for u in tier.pool_units if u.id == 'rg_2')
        assert_that(unit.type, equal_to(PoolUnitTypeEnum.RAID_GROUP))
        assert_that(unit.tier_type, equal_to(TierTypeEnum.PERFORMANCE))
        assert_that(unit.name, equal_to("RAID5, #2, pool:perfpool1130"))
        assert_that(unit.description, equal_to('123'))
        assert_that(unit.wwn, equal_to(
            '06:00:00:00:05:00:00:00:01:00:00:00:00:00:00:64'))
        assert_that(unit.size_total, equal_to(1181501882368))
        assert_that(unit.pool, instance_of(UnityPool))

    @patch_rest
    def test_get_nested_resource_filter_by_non_id(self):
        pools = UnityPoolList(cli=t_rest())
        pool = next(pool for pool in pools if pool.id == 'pool_1')
        tier = next(t for t in pool.tiers if t.name == 'Performance')
        unit = next(u for u in tier.pool_units if u.description == '123')
        assert_that(unit.id, equal_to('rg_2'))

    @patch_rest
    def test_create_pool(self):
        cli = t_rest()
        disk_group = UnityDiskGroup.get(cli=cli, _id='dg_15')
        raid_group_0 = RaidGroupParameter(
            disk_group=disk_group,
            disk_num=3, raid_type=RaidTypeEnum.RAID5,
            stripe_width=RaidStripeWidthEnum.BEST_FIT)
        raid_groups = [raid_group_0]
        pool = UnityPool.create(
            cli=cli, name='test_pool', description='Unity test pool.',
            raid_groups=raid_groups, alert_threshold=15,
            is_harvest_enabled=True, is_snap_harvest_enabled=True,
            pool_harvest_high_threshold=80, pool_harvest_low_threshold=40,
            snap_harvest_high_threshold=80, snap_harvest_low_threshold=40,
            is_fast_cache_enabled=True, is_fastvp_enabled=True,
            pool_type=StoragePoolTypeEnum.DYNAMIC)
        assert_that(pool.id, equal_to('pool_4'))
        assert_that(pool.pool_type, equal_to(StoragePoolTypeEnum.DYNAMIC))
        assert_that(pool.is_all_flash, equal_to(False))

    @patch_rest
    def test_create_pool_name_in_use(self):
        cli = t_rest()
        raid_group_0 = RaidGroupParameter(
            disk_group='dg_15',
            disk_num=3, raid_type=RaidTypeEnum.RAID5,
            stripe_width=RaidStripeWidthEnum.BEST_FIT)
        raid_groups = [raid_group_0]

        def _inner():
            UnityPool.create(
                cli=cli, name='duplicate_pool',
                description='Unity test pool.',
                raid_groups=raid_groups)

        assert_that(_inner, raises(UnityPoolNameInUseError))

    @patch_rest
    def test_extend_pool(self):
        cli = t_rest()
        raid_group_0 = RaidGroupParameter(
            disk_group='dg_8',
            disk_num=4,
            raid_type=RaidTypeEnum.RAID10,
            stripe_width=RaidStripeWidthEnum.BEST_FIT)
        raid_groups = [raid_group_0]
        pool0 = UnityPool.get(cli=cli, _id='pool_1')
        resp = pool0.modify(raid_groups=raid_groups)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_modify_pool(self):
        cli = t_rest()
        pool0 = UnityPool.get(cli=cli, _id='pool_30')
        resp = pool0.modify(name="new_name",
                            is_fastvp_enabled=True,
                            alert_threshold=80)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_pool(self):
        cli = t_rest()
        pool = UnityPool.get(cli=cli, _id='pool_4')
        resp = pool.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_create_filesystem_success(self):
        pool = UnityPool(_id='pool_1', cli=t_rest())
        fs = pool.create_filesystem(
            'nas_2', 'fs3', 3 * 1024 ** 3,
            proto=FSSupportedProtocolEnum.CIFS,
            tiering_policy=TieringPolicyEnum.AUTOTIER_HIGH)
        assert_that(fs.get_id(), equal_to('fs_12'))

    @patch_rest
    def test_create_lun(self):
        pool = UnityPool(_id='pool_1', cli=t_rest())
        lun = pool.create_lun("LunName", 100)
        assert_that(lun, instance_of(UnityLun))

    @patch_rest
    def test_create_lun_with_same_name(self):
        pool = UnityPool(_id='pool_1', cli=t_rest())

        def f():
            pool.create_lun("openstack_lun")

        assert_that(f, raises(UnityLunNameInUseError))

    @patch_rest
    def test_create_lun_on_spb(self):
        pool = UnityPool(_id='pool_1', cli=t_rest())
        sp = UnityStorageProcessor(_id='spb', cli=t_rest())
        lun = pool.create_lun("LunName", 100, sp=sp)
        assert_that(lun, instance_of(UnityLun))

    @patch_rest
    def test_create_lun_with_muitl_property(self):
        pool = UnityPool(_id='pool_1', cli=t_rest())
        lun = pool.create_lun("LunName", 100,
                              description="Hello World", is_thin=True,
                              is_repl_dst=True,
                              tiering_policy=TieringPolicyEnum.AUTOTIER_HIGH)
        assert_that(lun, instance_of(UnityLun))

    @patch_rest
    def test_create_lun_with_compression_enabled_v4_2(self):
        pool = UnityPool(_id='pool_1', cli=t_rest(version='4.2'))
        lun = pool.create_lun("LunName", 100,
                              is_compression=True)
        assert_that(lun, instance_of(UnityLun))

    @patch_rest
    def test_create_lun_with_compression_enabled(self):
        pool = UnityPool(_id='pool_1', cli=t_rest(version='4.3'))
        lun = pool.create_lun("LunName", 100,
                              is_compression=True)
        assert_that(lun, instance_of(UnityLun))

    @patch_rest
    def test_create_nfs_share_success(self):
        pool = UnityPool(_id='pool_5', cli=t_rest())
        nas_server = UnityNasServer.get(cli=t_rest(), _id='nas_6')
        job = pool.create_nfs_share(
            nas_server,
            name='513dd8b0-2c22-4da0-888e-494d320303b6',
            size=4294967296)
        assert_that(JobStateEnum.COMPLETED, equal_to(job.state))

    @patch_rest
    def test_create_nfs_share_failed(self):
        def f():
            pool = UnityPool(_id='pool_1', cli=t_rest())
            nas_server = UnityNasServer.get(cli=t_rest(), _id='nas_1')
            pool.create_nfs_share(
                nas_server,
                name='job_share_failed',
                size=1)

        assert_that(f, raises(JobStateError, 'too small'))
