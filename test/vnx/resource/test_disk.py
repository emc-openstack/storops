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

from hamcrest import assert_that, raises, equal_to, has_items, close_to

from storops.lib.common import instance_cache, cache
from test.vnx.cli_mock import patch_cli, t_cli
from test.vnx.resource.verifiers import verify_disk_4_0_e8
from storops.vnx.resource.disk import VNXDisk, VNXDiskList

__author__ = 'Cedric Zhuang'


@patch_cli
@cache
def get_disks():
    return VNXDisk.get(t_cli())


class VNXDiskTest(TestCase):
    def test_invalid_index(self):
        def f():
            VNXDisk('abcde')

        assert_that(f, raises(ValueError, 'invalid disk index'))

    def test_parse_index(self):
        bus, enc, disk = VNXDisk.parse_index('1_10_A4')
        assert_that(bus, equal_to("1"))
        assert_that(enc, equal_to("10"))
        assert_that(disk, equal_to("A4"))

    def test_parse_index_error(self):
        def f():
            VNXDisk.parse_index('abcdefg')

        assert_that(f, raises(ValueError, 'invalid disk index'))

    @patch_cli
    def test_get_all(self):
        disks = get_disks()
        assert_that(len(disks), equal_to(180))
        for disk in disks:
            if disk.index == '4_0_e8':
                verify_disk_4_0_e8(disk)
                break

    @patch_cli
    def test_get_disk(self):
        disk = VNXDisk.get(t_cli(), '4_0_e8')
        verify_disk_4_0_e8(disk)

    @property
    @instance_cache
    def disk_001(self):
        return VNXDisk('0_0_1', t_cli())

    @patch_cli
    def test_delete_disk(self):
        ret = self.disk_001.delete()
        assert_that(ret, has_items(''))

    @patch_cli
    def test_install_disk(self):
        ret = self.disk_001.install()
        assert_that(ret, has_items(''))

    @patch_cli
    def test_disk_read_iops(self):
        assert_that(self.disk_001.read_iops, equal_to(4.1))

    @patch_cli
    def test_disk_write_iops(self):
        assert_that(self.disk_001.write_iops, equal_to(5.1))

    @patch_cli
    def test_disk_total_iops(self):
        assert_that(self.disk_001.total_iops, equal_to(9.2))

    @patch_cli
    def test_disk_read_mbps(self):
        assert_that(self.disk_001.read_mbps, equal_to(3.2))

    @patch_cli
    def test_disk_write_mbps(self):
        assert_that(self.disk_001.write_mbps, equal_to(4.2))

    @patch_cli
    def test_disk_total_mbps(self):
        assert_that(self.disk_001.total_mbps, equal_to(7.4))

    @patch_cli
    def test_disk_utilization(self):
        assert_that(self.disk_001.utilization, equal_to(40.0))

    @patch_cli
    def test_disk_read_size_kb(self):
        assert_that(self.disk_001.read_size_kb, close_to(799.0, 1))

    @patch_cli
    def test_disk_write_size_kb(self):
        assert_that(self.disk_001.write_size_kb, close_to(844.0, 1))


class VNXDiskListTest(TestCase):
    disk_indices = ['0_0_C8', '4_0_D0', '4_0_E8']

    @patch_cli
    def test_all(self):
        disks = get_disks()
        assert_that(len(disks), equal_to(180))

    @patch_cli
    def test_index_filter(self):
        disks = get_disks().shadow_copy(disk_indices=self.disk_indices)
        assert_that(len(disks), equal_to(3))

    @patch_cli
    def test_multiple_filters(self):
        disks = get_disks().shadow_copy()
        disks.set_drive_type('NL SAS')
        assert_that(len(disks), equal_to(42))
        disks.set_capacity(2817564)
        assert_that(len(disks), equal_to(40))

    @patch_cli
    def test_get_same_disks_available(self):
        disks = get_disks().shadow_copy(disk_indices=self.disk_indices)
        disks.same_disks(2)
        assert_that(len(disks), equal_to(2))

    @patch_cli
    def test_get_same_disks_not_available(self):
        disks = get_disks().shadow_copy(disk_indices=self.disk_indices)
        disks.same_disks(3)
        assert_that(len(disks), equal_to(0))

    def test_resource_class_name(self):
        assert_that(VNXDiskList.resource_class_name(), equal_to('VNXDisk'))
