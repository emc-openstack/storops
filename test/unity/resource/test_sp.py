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

import os
from os import path
from unittest import TestCase

from hamcrest import assert_that, equal_to, instance_of, only_contains, \
    raises, contains_string, greater_than, is_not

from storops.lib.common import get_file_size, get_local_folder
from storops.unity.enums import NodeEnum
from storops.unity.resource.health import UnityHealth
from storops.unity.resource.sp import UnityStorageProcessor, \
    UnityStorageProcessorList
from storops.unity.resource.system import UnityDpe, UnitySystem
from test.unity.rest_mock import t_rest, patch_rest, t_unity

__author__ = 'Cedric Zhuang'


class UnityStorageProcessorTest(TestCase):

    @property
    @patch_rest
    def sp_list(self):
        return t_unity().get_sp()

    @patch_rest
    def test_properties(self):
        sp = UnityStorageProcessor(_id='spa', cli=t_rest())
        assert_that(sp.id, equal_to('spa'))
        assert_that(sp.existed, equal_to(True))
        assert_that(sp.health, instance_of(UnityHealth))
        assert_that(sp.needs_replacement, equal_to(False))
        assert_that(sp.is_rescue_mode, equal_to(False))
        assert_that(sp.model, equal_to('OBERON CANISTER 10C 105W 2.6G'))
        assert_that(sp.slot_number, equal_to(0))
        assert_that(sp.name, equal_to('SP A'))
        assert_that(sp.emc_part_number, equal_to('110-297-008C-04'))
        assert_that(sp.emc_serial_number, equal_to('CF2HF150300001'))
        assert_that(sp.manufacturer, equal_to(''))
        assert_that(sp.vendor_part_number, equal_to(''))
        assert_that(sp.vendor_serial_number, equal_to(''))
        assert_that(sp.sas_expander_version, equal_to('2.7.1'))
        assert_that(sp.bios_firmware_revision, equal_to('30.89'))
        assert_that(sp.post_firmware_revision, equal_to('21.2'))
        assert_that(sp.memory_size, equal_to(65536))
        assert_that(sp.parent_dpe, instance_of(UnityDpe))

    @patch_rest
    def test_sp_to_node_enum(self):
        sp = UnityStorageProcessor(_id='spa', cli=t_rest())
        assert_that(sp.to_node_enum(), equal_to(NodeEnum.SPA))
        sp = UnityStorageProcessor(_id='spb', cli=t_rest())
        assert_that(sp.to_node_enum(), equal_to(NodeEnum.SPB))
        sp = UnityStorageProcessor(_id='wrong', cli=t_rest())
        assert_that(sp.to_node_enum(), equal_to(NodeEnum.UNKNOWN))

    @patch_rest
    def test_get_all_and_property_query(self):
        sp_list = UnityStorageProcessorList(cli=t_rest())
        assert_that(len(sp_list), equal_to(2))
        assert_that(sp_list.name, only_contains('SP A', 'SP B'))

    @patch_rest
    def test_get_all_and_property_not_found(self):
        def f():
            sp_list = UnityStorageProcessorList(cli=t_rest())
            return sp_list.not_found

        assert_that(f, raises(AttributeError, 'not_found'))

    @patch_rest
    def test_metric_utilization(self):
        spa, spb = self.sp_list
        assert_that(spa.utilization, equal_to(22))
        assert_that(spb.utilization, equal_to(33))

    @patch_rest
    def test_metric_nfs_write_mbps(self):
        spa, spb = self.sp_list
        assert_that(spa.nfs_write_mbps, equal_to(3.9))
        assert_that(spb.nfs_write_mbps, equal_to(4.1))

    @patch_rest
    def test_metric_nfs_read_mbps(self):
        spa, spb = self.sp_list
        assert_that(spa.nfs_read_mbps, equal_to(3.7))
        assert_that(spb.nfs_read_mbps, equal_to(3.8))

    @patch_rest
    def test_metric_nfs_write_iops(self):
        spa, spb = self.sp_list
        assert_that(spa.nfs_write_iops, equal_to(3.5))
        assert_that(spb.nfs_write_iops, equal_to(3.6))

    @patch_rest
    def test_metric_nfs_read_iops(self):
        spa, spb = self.sp_list
        assert_that(spa.nfs_read_iops, equal_to(3.3))
        assert_that(spb.nfs_read_iops, equal_to(3.4))

    @patch_rest
    def test_metric_cifs_write_mbps(self):
        spa, spb = self.sp_list
        assert_that(spa.cifs_write_mbps, equal_to(3.1))
        assert_that(spb.cifs_write_mbps, equal_to(3.2))

    @patch_rest
    def test_metric_cifs_read_mbps(self):
        spa, spb = self.sp_list
        assert_that(spa.cifs_read_mbps, equal_to(2.8))
        assert_that(spb.cifs_read_mbps, equal_to(2.9))

    @patch_rest
    def test_metric_cifs_write_iops(self):
        spa, spb = self.sp_list
        assert_that(spa.cifs_write_iops, equal_to(2.6))
        assert_that(spb.cifs_write_iops, equal_to(2.7))

    @patch_rest
    def test_metric_cifs_read_iops(self):
        spa, spb = self.sp_list
        assert_that(spa.cifs_read_iops, equal_to(2.4))
        assert_that(spb.cifs_read_iops, equal_to(2.5))

    @patch_rest
    def test_metric_block_write_mbps(self):
        spa, spb = self.sp_list
        assert_that(spa.block_write_mbps, equal_to(30))
        assert_that(spb.block_write_mbps, equal_to(40))

    @patch_rest
    def test_metric_block_read_mbps(self):
        spa, spb = self.sp_list
        assert_that(spa.block_read_mbps, equal_to(1.9))
        assert_that(spb.block_read_mbps, equal_to(2.1))

    @patch_rest
    def test_metric_block_write_iops(self):
        spa, spb = self.sp_list
        assert_that(spa.block_write_iops, equal_to(1.7))
        assert_that(spb.block_write_iops, equal_to(1.8))

    @patch_rest
    def test_metric_block_read_iops(self):
        spa, spb = self.sp_list
        assert_that(spa.block_read_iops, equal_to(1.5))
        assert_that(spb.block_read_iops, equal_to(1.6))

    @patch_rest
    def test_metric_temperature(self):
        spa, spb = self.sp_list
        assert_that(spa.temperature, equal_to(27))
        assert_that(spb.temperature, equal_to(28))

    @patch_rest
    def test_metric_core_count(self):
        spa, spb = self.sp_list
        assert_that(spa.core_count, equal_to(10))
        assert_that(spa.core_count, equal_to(10))

    @patch_rest
    def test_metric_net_out_mbps(self):
        spa, spb = self.sp_list
        assert_that(spa.net_out_mbps, equal_to(1.3))
        assert_that(spb.net_out_mbps, equal_to(1.4))

    @patch_rest
    def test_metric_net_in_mbps(self):
        spa, spb = self.sp_list
        assert_that(spa.net_in_mbps, equal_to(1.1))
        assert_that(spb.net_in_mbps, equal_to(1.2))

    @patch_rest
    def test_metric_block_cache_read_hit_ratio(self):
        spa, spb = self.sp_list
        assert_that(spa.block_cache_read_hit_ratio, equal_to(87.0))
        assert_that(spb.block_cache_read_hit_ratio, equal_to(88.0))

    @patch_rest
    def test_metric_block_cache_write_hit_ratio(self):
        spa, spb = self.sp_list
        assert_that(spa.block_cache_write_hit_ratio, equal_to(89.0))
        assert_that(spb.block_cache_write_hit_ratio, equal_to(90.0))

    @patch_rest
    def test_csv(self):
        csv = self.sp_list.get_metrics_csv()
        assert_that(csv, contains_string('timestamp,id,name,'))
        assert_that(csv, contains_string('block_read_iops,block_read_mbps'))
        assert_that(csv, contains_string('2016-11-21 09:10:00+00:00,spa'))
        assert_that(csv, contains_string('spa,SP A,87.0,89.0'))
        assert_that(csv, contains_string('spb,SP B,88.0,90.0'))

    FILENAME = path.join(get_local_folder(),
                         'unittest_sp_metric_persist_csv_file.csv')

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.FILENAME):
            os.remove(cls.FILENAME)

    @patch_rest
    def test_persist_csv(self):
        self.sp_list.persist_metric_data(self.FILENAME)
        assert_that(os.path.exists(self.FILENAME), equal_to(True))
        file_size = get_file_size(self.FILENAME)

        self.sp_list.persist_metric_data(self.FILENAME)
        new_file_size = get_file_size(self.FILENAME)
        assert_that(new_file_size, greater_than(file_size))

    @patch_rest
    def test_repr_with_metric(self):
        spa, _ = self.sp_list
        assert_that(str(spa), contains_string('"nfs_write_mbps":'))

    @patch_rest
    def test_repr_without_metric(self):
        spa, _ = UnitySystem('10.244.223.61').get_sp()
        assert_that(str(spa), is_not(contains_string('"nfs_write_mbps":')))

    @patch_rest
    def test_default_metric_csv_filename(self):
        sp_list = UnitySystem('10.244.223.61').get_sp()
        filename = sp_list.get_default_metric_csv_filename()
        assert_that(filename, contains_string('.storops'))
        assert_that(filename,
                    contains_string('10.244.223.61_storageProcessor.csv'))
