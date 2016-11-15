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

from hamcrest import assert_that, equal_to, has_items, close_to, \
    contains_string

from storops import DiskTechnologyEnum, TierTypeEnum
from storops.unity.resource.disk import UnityDiskList, UnityDisk
from test.unity.rest_mock import t_rest, patch_rest, t_unity

__author__ = 'Cedric Zhuang'


class UnityDiskTest(TestCase):
    @patch_rest
    def test_get_all(self):
        disks = UnityDiskList(cli=t_rest())
        assert_that(len(disks), equal_to(40))
        self.verify_dae_0_1_disk_0(
            *filter(lambda d: d.id == 'dae_0_1_disk_0', disks))

    @patch_rest
    def test_properties(self):
        disk = UnityDisk(_id='dae_0_1_disk_0', cli=t_rest())
        self.verify_dae_0_1_disk_0(disk)

    def verify_dae_0_1_disk_0(self, disk):
        assert_that(disk.id, equal_to('dae_0_1_disk_0'))
        assert_that(disk.bus_id, equal_to(0))
        assert_that(disk.current_speed, equal_to(12000000000))
        assert_that(disk.disk_technology, equal_to(DiskTechnologyEnum.NL_SAS))
        assert_that(disk.emc_part_number, equal_to('005051284'))
        assert_that(disk.emc_serial_number, equal_to('Z4H027TW'))
        assert_that(disk.is_fast_cache_in_use, equal_to(False))
        assert_that(disk.is_in_use, equal_to(False))
        assert_that(disk.is_sed, equal_to(False))
        assert_that(disk.manufacturer, equal_to('SEAGATE'))
        assert_that(disk.max_speed, equal_to(12000000000))
        assert_that(disk.model, equal_to('ST2000NK EMC2000'))
        assert_that(disk.name, equal_to('DAE 0 1 Disk 0'))
        assert_that(disk.needs_replacement, equal_to(False))
        assert_that(disk.raw_size, equal_to(1969623564288))
        assert_that(disk.rpm, equal_to(7200))
        assert_that(disk.size, equal_to(1969590009856))
        assert_that(disk.slot_number, equal_to(0))
        assert_that(disk.tier_type, equal_to(TierTypeEnum.CAPACITY))
        assert_that(disk.vendor_size, equal_to(2199023255552))
        assert_that(disk.version, equal_to('MN16'))
        assert_that(disk.wwn, equal_to(
            '06:00:00:00:05:00:00:00:0C:01:00:00:00:00:00:03'))
        assert_that(disk.inserted, equal_to(True))

    def test_metric_names(self):
        metric_names = UnityDisk().metric_names()
        assert_that(metric_names, has_items('read_iops', 'write_iops'))

    @patch_rest
    def test_not_inserted(self):
        disk = UnityDisk(_id='dpe_disk_23', cli=t_rest())
        assert_that(disk.inserted, equal_to(False))

    @patch_rest
    def test_metric_read_iops(self):
        unity = t_unity()
        disk = UnityDisk(_id='dae_0_1_disk_2', cli=unity._cli)
        assert_that(disk.write_iops, close_to(0.0, 0.01))

    @patch_rest
    def test_metric_in_repr(self):
        unity = t_unity()
        disk = UnityDisk(_id='dae_0_1_disk_2', cli=unity._cli)
        repr_str = repr(disk)
        assert_that(repr_str, contains_string('"read_iops":'))
        assert_that(repr_str, contains_string('"write_mbps"'))

    @patch_rest
    def test_disk_list_metrics(self):
        unity = t_unity()
        disks = UnityDiskList(cli=unity._cli)
        assert_that(len(disks), equal_to(40))

    @patch_rest
    def test_disk_utilization(self):
        unity = t_unity()
        disk = UnityDisk(_id='dae_0_1_disk_2', cli=unity._cli)
        assert_that(disk.utilization, close_to(2.41, 0.01))

    @patch_rest
    def test_get_disk_inserted_list(self):
        disks = UnityDiskList(cli=t_rest(), inserted=True)
        ret = set(disks.inserted)
        assert_that(ret, equal_to({True}))
        assert_that(len(disks), equal_to(26))
