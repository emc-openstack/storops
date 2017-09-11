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
from __future__ import unicode_literals, division

from unittest import TestCase

from hamcrest import assert_that, has_items, equal_to, raises, has_item, \
    close_to, is_not

from storops.unity import calculator
from storops.unity.calculator import calculators, IdValues, \
    delta_ps, mb_ps_by_block, busy_idle_util, \
    sp_delta_ps, sp_mb_ps_by_byte, sp_mb_ps_by_block, sp_busy_idle_util, \
    only_one_path, sp_fact, all_not_none, UnityMetricConfig, \
    UnityMetricConfigParser, total_delta_ps, sp_total_delta_ps, \
    system_delta_ps, system_total_delta_ps, disk_response_time, \
    disk_queue_length, lun_response_time, lun_queue_length, \
    sp_sum_values, sp_io_rate, byte_rate, total_byte_rate, sp_byte_rate, \
    sp_total_byte_rate, system_byte_rate, system_total_byte_rate
from storops.unity.resource.disk import UnityDisk
from storops.unity.resource.filesystem import UnityFileSystem
from storops_test.unity.resource.test_metric import qr_6, qr_14, qr_17, \
    qr_34, qr_128, qr_130
from storops_test.unity.rest_mock import patch_rest
from storops_test.utils import is_nan

__author__ = 'Cedric Zhuang'


class MockCli(object):
    def __init__(self, prev, curr):
        self.prev_counter = prev
        self.curr_counter = curr


class CalculatorMetaInfoTest(TestCase):
    def test_get_metric_names(self):
        names = calculators.get_metric_names(UnityDisk)
        assert_that(names, has_items(
            'read_iops', 'write_iops', 'read_mbps', 'write_mbps'))

    def test_all_paths_default(self):
        paths = calculators.get_all_paths()
        assert_that(paths, has_items(
            'sp.*.physical.disk.*.reads',
            'sp.*.physical.disk.*.writes',
            'sp.*.physical.disk.*.readBlocks',
            'sp.*.physical.disk.*.writeBlocks',
            'sp.*.cpu.summary.busyTicks',
            'sp.*.storage.filesystem.*.reads',
            'sp.*.storage.lun.*.reads'))

    def test_all_paths_with_clz_list(self):
        paths = calculators.get_all_paths([UnityDisk, UnityFileSystem])
        assert_that(paths, has_items(
            'sp.*.physical.disk.*.reads',
            'sp.*.storage.filesystem.*.reads'))
        assert_that(paths, is_not(has_item('sp.*.cpu.summary.busyTicks')))
        assert_that(paths, is_not(has_item('sp.*.storage.lun.*.reads')))

    def test_get_calculator_of_metric(self):
        calc = calculators.get_calculator('UnityDisk', 'read_iops')
        assert_that(calc, equal_to(delta_ps))

    @patch_rest
    def test_get_metric_value_normal(self):
        disk_counters = MockCli(qr_6, qr_14)
        value = calculators.get_metric_value(
            UnityDisk, 'read_iops', disk_counters, 'dae_0_1_disk_2')
        expected = ((4158667 + 5) - (2966780 + 5)) / 163800.0
        assert_that(value, equal_to(expected))

    @patch_rest
    def test_get_metric_value_no_prev_data(self):
        disk_counters = MockCli(None, qr_6)
        value = calculators.get_metric_value(
            UnityDisk, 'read_iops', disk_counters, 'dae_0_1_disk_2')
        assert_that(value, is_nan())


class IdValuesTest(TestCase):
    def setUp(self):
        self.o1 = IdValues({'a': 2, 'b': 3})
        self.o2 = IdValues({'a': 7, 'c': 13})
        self.o3 = IdValues({'a': None, 'b': 17})

    def test_add_none(self):
        o1 = self.o1
        r = o1 + None
        assert_that(o1['a'], equal_to(2))
        assert_that(o1['b'], equal_to(3))
        assert_that(r['a'], equal_to(2))
        assert_that(r['b'], equal_to(3))
        r.set('a', 5)
        assert_that(o1['a'], equal_to(2))
        assert_that(r['a'], equal_to(5))

    def test_sum(self):
        r = sum([self.o1, self.o2, self.o3])
        assert_that(r['a'], equal_to(9))
        assert_that(r['b'], equal_to(20))
        assert_that(r['c'], equal_to(13))

    def test_self_add(self):
        r = self.o1.copy()
        r += self.o2
        assert_that(r['a'], equal_to(9))
        assert_that(r['b'], equal_to(3))
        assert_that(r['c'], equal_to(13))

    def test_add_has_none(self):
        r = self.o1 + self.o3
        assert_that(r['a'], equal_to(2))
        assert_that(r['b'], equal_to(20))

    def test_radd_none(self):
        o1 = self.o1
        r = None + o1
        assert_that(o1['a'], equal_to(2))
        assert_that(o1['b'], equal_to(3))
        assert_that(r['a'], equal_to(2))
        assert_that(r['b'], equal_to(3))
        r.set('a', 5)
        assert_that(o1['a'], equal_to(2))
        assert_that(r['a'], equal_to(5))

    def test_add_id_value(self):
        o1 = self.o1
        o2 = self.o2
        r = o1 + o2
        assert_that(o1['a'], equal_to(2))
        assert_that(o1['b'], equal_to(3))
        assert_that(len(o1), equal_to(2))
        assert_that(r['a'], equal_to(9))
        assert_that(r['b'], equal_to(3))
        assert_that(r['c'], equal_to(13))
        assert_that(len(r), equal_to(3))

    def test_add_int(self):
        o1 = self.o1
        r = o1 + 5
        assert_that(o1['a'], equal_to(2))
        assert_that(o1['b'], equal_to(3))
        assert_that(len(o1), equal_to(2))
        assert_that(r['a'], equal_to(7))
        assert_that(r['b'], equal_to(8))
        assert_that(len(r), equal_to(2))

    def test_radd_float(self):
        o1 = self.o1
        r = 5.1 + o1
        assert_that(o1['a'], equal_to(2))
        assert_that(o1['b'], equal_to(3))
        assert_that(len(o1), equal_to(2))
        assert_that(r['a'], equal_to(7.1))
        assert_that(r['b'], equal_to(8.1))
        assert_that(len(r), equal_to(2))

    def test_sub_id_values(self):
        r = self.o2 - self.o1
        assert_that(self.o2['a'], equal_to(7))
        assert_that(self.o2['c'], equal_to(13))
        assert_that(r['a'], equal_to(5))
        assert_that(r['b'], equal_to(-3))
        assert_that(r['c'], equal_to(13))

    def test_rsub_none(self):
        r = None - self.o1
        assert_that(r['a'], equal_to(-2))
        assert_that(r['b'], equal_to(-3))

    def test_rsub_float(self):
        r = 9.5 - self.o1
        assert_that(r['a'], equal_to(7.5))
        assert_that(r['b'], equal_to(6.5))

    def test_add_from_empty(self):
        r = IdValues() + self.o1
        assert_that(r['a'], equal_to(2))
        assert_that(r['b'], equal_to(3))

    def test_div_id_value(self):
        r = self.o1 / self.o2
        assert_that(r['a'], equal_to(2.0 / 7.0))
        assert_that(r['b'], is_nan())
        assert_that(r['c'], is_nan())

    def test_div_numeric(self):
        r = self.o1 / 2
        assert_that(r['a'], equal_to(1.0))
        assert_that(r['b'], equal_to(1.5))

    def test_div_by_zero(self):
        r = self.o1 / 0
        assert_that(r['a'], is_nan())
        assert_that(r['b'], is_nan())

    def test_div_zero_dev(self):
        r = 0.0 / IdValues({'a': 0, 'b': 3})
        assert_that(r['a'], equal_to(0.0))
        assert_that(r['b'], equal_to(0.0))

    def test_div_by_partial_zero(self):
        r = self.o1 / IdValues({'a': 2, 'b': 0})
        assert_that(r['a'], equal_to(1.0))
        assert_that(r['b'], is_nan())

    def test_rdiv_numerical(self):
        r = 12 / self.o1
        assert_that(r['a'], equal_to(6))
        assert_that(r['b'], equal_to(4))

    def test_rdiv_none(self):
        r = None / self.o1
        assert_that(r['a'], is_nan())
        assert_that(r['b'], is_nan())

    def test_mul_none(self):
        r = self.o1 * None
        assert_that(r['a'], equal_to(2))
        assert_that(r['b'], equal_to(3))

    def test_rmul_none(self):
        r = None * self.o1
        assert_that(r['a'], equal_to(2))
        assert_that(r['b'], equal_to(3))

    def test_mul_numerical(self):
        r = self.o1 * 3
        assert_that(r['a'], equal_to(6))
        assert_that(r['b'], equal_to(9))

    def test_rmul_numerical(self):
        r = 3 * self.o1
        assert_that(r['a'], equal_to(6))
        assert_that(r['b'], equal_to(9))

    def test_mul_id_values(self):
        r = self.o1 * self.o2
        assert_that(r['a'], equal_to(14))
        assert_that(r['b'], equal_to(3))
        assert_that(r['c'], equal_to(13))

    def test_mul_partial_none(self):
        r = self.o1 * self.o3
        assert_that(r['a'], equal_to(2))
        assert_that(r['b'], equal_to(51))


class CalculatorTest(TestCase):
    @patch_rest
    def test_disk_read_iops(self):
        ret = delta_ps('sp.*.physical.disk.*.reads', qr_6, qr_14)
        expected = ((4158667 + 5) - (2966780 + 5)) / 163800.0
        assert_that(ret['dae_0_1_disk_2'], equal_to(expected))

        assert_that(delta_ps('sp.*.physical.disk.*.reads', qr_6, qr_14,
                             'dae_0_1_disk_2'),
                    equal_to(expected))

    @patch_rest
    def test_disk_read_obj_not_found(self):
        ret = delta_ps('sp.*.physical.disk.*.reads', qr_6, qr_14,
                       'not_found')
        assert_that(ret, is_nan())

    @patch_rest
    def test_disk_write_iops(self):
        ret = delta_ps('sp.*.physical.disk.*.writes', qr_6, qr_14)
        expected = ((3762339 + 5) - (2679611 + 5)) / 163800.0
        assert_that(ret['dae_0_1_disk_2'], equal_to(expected))

    @patch_rest
    def test_path_not_found(self):
        ret = mb_ps_by_block('sp.*.physical.disk.*.writeBlocks', qr_6, qr_14)
        assert_that(ret['dae_0_1_disk_2'], is_nan())

        ret = mb_ps_by_block(
            'sp.*.physical.disk.*.writeBlocks', qr_6, qr_14, 'dae_0_1_disk_2')
        assert_that(ret, is_nan())

    @patch_rest
    def test_mb_ps_by_block_value(self):
        ret = mb_ps_by_block('sp.*.physical.disk.*.writeBlocks', qr_17, qr_34)
        assert_that(ret['dae_0_1_disk_0'], equal_to(5.0))

    def test_delta_ps_error_path(self):
        def f():
            delta_ps(['a', 'b'], None, None)

        assert_that(f, raises(ValueError, 'only one path'))

    @patch_rest
    def test_disk_utilization_all(self):
        paths = ['sp.*.physical.disk.*.busyTicks',
                 'sp.*.physical.disk.*.idleTicks']
        ret = busy_idle_util(paths, qr_17, qr_34)
        expected = self.expected_disk_utilization()
        assert_that(ret['dae_0_1_disk_0'], equal_to(expected))
        assert_that(ret['dpe_disk_24'], is_nan())

    @patch_rest
    def test_disk_utilization_single(self):
        paths = ['sp.*.physical.disk.*.busyTicks',
                 'sp.*.physical.disk.*.idleTicks']
        ret = busy_idle_util(paths, qr_17, qr_34, 'dae_0_1_disk_0')
        expected = self.expected_disk_utilization()
        assert_that(ret, equal_to(expected))

    @patch_rest
    def test_disk_utilization_nan_single(self):
        paths = ['sp.*.physical.disk.*.busyTicks',
                 'sp.*.physical.disk.*.idleTicks']
        ret = busy_idle_util(paths, qr_17, qr_34, 'dpe_disk_24')
        assert_that(ret, is_nan())

    def expected_disk_utilization(self):
        busy = (55249062767 + 631119255518) - (55243132789 + 630939312447)
        idle = (609018780542 + 0) - (608836882713 + 0)
        return busy * 100.0 / (idle + busy)

    @patch_rest
    def test_sp_delta_ps_all(self):
        ret = sp_delta_ps('sp.*.cifs.smb1.basic.writes', qr_17, qr_34)
        assert_that(ret['spa'], close_to(2.77, 0.01))
        assert_that(ret['spb'], close_to(5.55, 0.01))

    @patch_rest
    def test_sp_delta_ps_obj(self):
        ret = sp_delta_ps('sp.*.cifs.smb1.basic.writes', qr_17, qr_34, 'spa')
        assert_that(ret, close_to(2.77, 0.01))

        ret = sp_delta_ps('sp.*.cifs.smb1.basic.writes', qr_17, qr_34, 'spc')
        assert_that(ret, is_nan())

    @patch_rest
    def test_sp_mb_ps_by_byte_all(self):
        ret = sp_mb_ps_by_byte('sp.*.cifs.smb1.basic.writeBytes', qr_17, qr_34)
        assert_that(ret['spa'], equal_to(1.0))
        assert_that(ret['spb'], equal_to(2.0))

    @patch_rest
    def test_sp_mb_ps_by_block_all(self):
        ret = sp_mb_ps_by_block(
            'sp.*.storage.summary.writeBlocks', qr_17, qr_34)
        assert_that(ret['spa'], equal_to(30.0))
        assert_that(ret['spb'], equal_to(40.0))

    @patch_rest
    def test_sp_busy_idle_util(self):
        paths = ['sp.*.cpu.summary.busyTicks',
                 'sp.*.cpu.summary.idleTicks']
        ret = sp_busy_idle_util(paths, qr_17, qr_34)
        assert_that(ret['spa'], equal_to(22.0))
        assert_that(ret['spb'], equal_to(33.0))

    @patch_rest
    def test_sp_temperature(self):
        path = 'sp.*.platform.storageProcessorTemperature'
        ret = sp_fact(path, qr_17, qr_34)
        assert_that(ret['spa'], equal_to(27))
        assert_that(ret['spb'], equal_to(28))

    def test_only_one_path_set(self):
        assert_that(only_one_path({'abc'}), equal_to('abc'))

    def test_only_one_path_error(self):
        def f():
            return only_one_path(('a', 'b'))

        assert_that(f, raises(ValueError, 'only one path'))

    def test_all_not_none(self):
        assert_that(all_not_none(1, 'a', 2.3), equal_to(True))
        assert_that(all_not_none(1, 'a', None, 2.3), equal_to(False))

    @patch_rest
    def test_total_delta_ps(self):
        path = ['sp.*.physical.disk.*.reads',
                'sp.*.physical.disk.*.writes']
        ret = total_delta_ps(path, qr_6, qr_14)

        delta_reads = (4158667 + 5) - (2966780 + 5)
        delta_writes = (3762339 + 5) - (2679611 + 5)
        diff_time = 163800.0

        expected = (delta_reads + delta_writes) / diff_time
        assert_that(ret['dae_0_1_disk_2'], close_to(expected, 0.01))

        assert_that(total_delta_ps(path, qr_6, qr_14, 'dae_0_1_disk_2'),
                    close_to(expected, 0.01))

    def test_total_delta_ps_error_path(self):
        def f():
            total_delta_ps(['a', 'b', 'c'], None, None)

        assert_that(f, raises(ValueError,
                              'takes in "reads" and "writes" counter.'))

    @patch_rest
    def test_sp_total_delta_ps(self):
        path = ['sp.*.storage.summary.reads',
                'sp.*.storage.summary.writes']
        ret = sp_total_delta_ps(path, qr_17, qr_34)

        diff_time = 180.0
        expected_spa = ((270 - 0) + (306 - 0)) / diff_time
        expected_spb = ((296 - 8) + (324 - 0)) / diff_time
        assert_that(ret['spa'], close_to(expected_spa, 0.01))
        assert_that(ret['spb'], close_to(expected_spb, 0.01))

        assert_that(sp_total_delta_ps(path, qr_17, qr_34, 'spa'),
                    close_to(expected_spa, 0.01))
        assert_that(sp_total_delta_ps(path, qr_17, qr_34, 'spb'),
                    close_to(expected_spb, 0.01))

    def test_sp_total_delta_ps_error_path(self):
        def f():
            sp_total_delta_ps(['a', 'b', 'c'], None, None)

        assert_that(f, raises(ValueError,
                              'takes in "reads" and "writes" counter.'))

    @patch_rest
    def test_system_delta_ps(self):
        path = 'sp.*.storage.summary.reads'
        ret = system_delta_ps(path, qr_17, qr_34)

        diff_time = 180.0
        expected = ((270 - 0) + (296 - 8)) / diff_time
        assert_that(ret['0'], close_to(expected, 0.01))

    def test_system_delta_ps_error_path(self):
        def f():
            system_delta_ps(['a', 'b'], None, None)

        assert_that(f, raises(ValueError, 'takes in one and only one path.'))

    @patch_rest
    def test_system_total_delta_ps(self):
        path = ['sp.*.storage.summary.reads',
                'sp.*.storage.summary.writes']
        ret = system_total_delta_ps(path, qr_17, qr_34)

        delta_total_reads = (270 - 0) + (296 - 8)
        delta_total_writes = (306 - 0) + (324 - 0)
        diff_time = 180.0

        expected = (delta_total_reads + delta_total_writes) / diff_time
        assert_that(ret['0'], close_to(expected, 0.01))

    def test_system_total_delta_ps_error_path(self):
        def f():
            system_total_delta_ps(['a', 'b', 'c'], None, None)

        assert_that(f, raises(ValueError,
                              'takes in "reads" and "writes" counter.'))

    @patch_rest
    def test_disk_response_time(self):
        path = ['sp.*.physical.disk.*.busyTicks',
                'sp.*.physical.disk.*.sumArrivalQueueLength',
                'sp.*.physical.disk.*.reads',
                'sp.*.physical.disk.*.writes',
                'sp.*.physical.coreCount']
        ret = disk_response_time(path, qr_128, qr_130)

        delta_busy_ticks = (151624601961 + 3485236370346) - \
                           (149509372140 + 3436715092500)
        delta_sum_ql = (3532917 + 705) - (3484428 + 705)
        delta_reads = (3532917 + 704) - (3484427 + 704)
        delta_writes = (0 + 0) - (0 + 0)
        delta_size_reads = (3532917 - 3484427) * 10 + (704 - 704) * 10
        delta_size_writes = (0 - 0) * 10 + (0 - 0) * 10

        expected = (delta_busy_ticks * delta_sum_ql) / \
                   ((delta_reads + delta_writes) *
                    (delta_size_reads + delta_size_writes))
        assert_that(ret['dae_0_1_disk_1'], close_to(expected, 0.01))

    def test_disk_response_time_error_path(self):
        def f():
            disk_response_time(['a', 'b', 'c', 'd', 'e', 'f'], None, None)

        assert_that(f, raises(ValueError,
                              'takes in "busyTicks", "sumArrivalQueueLength",'
                              ' "reads", "writes" and "coreCount" counter.'))

    @patch_rest
    def test_disk_queue_length(self):
        path = ['sp.*.physical.disk.*.sumArrivalQueueLength',
                'sp.*.physical.disk.*.reads',
                'sp.*.physical.disk.*.writes']
        ret = disk_queue_length(path, qr_128, qr_130)

        delta_sum_ql = (3532917 + 705) - (3484428 + 705)
        delta_reads = (3532917 + 704) - (3484427 + 704)
        delta_writes = (0 + 0) - (0 + 0)

        expected = delta_sum_ql / (delta_reads + delta_writes)
        assert_that(ret['dae_0_1_disk_1'], close_to(expected, 0.01))

    def test_disk_queue_length_error_path(self):
        def f():
            disk_queue_length(['a', 'b', 'c', 'd'], None, None)

        msg = 'takes in "sumArrivalQueueLength", "reads" and "writes" counter.'
        assert_that(f, raises(ValueError, msg))

    @patch_rest
    def test_lun_response_time(self):
        path = ['sp.*.storage.lun.*.totalIoTime',
                'sp.*.storage.lun.*.reads',
                'sp.*.storage.lun.*.writes']
        ret = lun_response_time(path, qr_128, qr_130)

        delta_sum_ql = (13012626542 + 27073895) - (12782881910 + 26805216)
        delta_reads = (166979 + 0) - (164007 + 0)
        delta_writes = (1618548 + 213) - (1596862 + 213)

        expected = delta_sum_ql / (delta_reads + delta_writes)
        assert_that(ret['sv_4'], close_to(expected, 0.01))

    def test_lun_response_time_error_path(self):
        def f():
            lun_response_time(['a', 'b', 'c', 'd'], None, None)

        msg = 'takes in "totalIoTime", "reads" and "writes" counter.'
        assert_that(f, raises(ValueError, msg))

    @patch_rest
    def test_lun_queue_length(self):
        path = ['sp.*.storage.lun.*.currentIOCount',
                'sp.*.storage.lun.*.busyTime',
                'sp.*.storage.lun.*.idleTime']
        ret = lun_queue_length(path, qr_128, qr_130)

        delta_io = (0 + 0) - (0 + 0)
        delta_busy = (319229585 + 1193127357) - (314779461 + 1176806087)
        delta_idle = (2989316155 + 3185505629) - (4117396013 + 4325740825)

        expected = delta_io * delta_busy / (delta_busy + delta_idle)
        assert_that(ret['sv_4'], close_to(expected, 0.01))

    def test_lun_queue_length_error_path(self):
        def f():
            lun_queue_length(['a', 'b', 'c', 'd'], None, None)

        msg = 'takes in "currentIOCount", "busyTime" and "idleTime" counter.'
        assert_that(f, raises(ValueError, msg))

    @patch_rest
    def test_sp_sum_values(self):
        path = 'sp.*.fastCache.volume.*.readHits'
        ret = sp_sum_values(path, qr_128, qr_130)
        expected_spa = 1000 + 2000 + 3000 + 4000 + 5000
        assert_that(ret['spa'], equal_to(expected_spa))
        expected_spb = 2000 + 4000 + 6000 + 8000 + 10000
        assert_that(ret['spb'], equal_to(expected_spb))

    def test_sp_sum_values_error_path(self):
        def f():
            sp_sum_values(['a', 'b'], None, None)

        assert_that(f, raises(ValueError, 'takes in one and only one path.'))

    @patch_rest
    def test_sp_io_rate(self):
        path = 'sp.*.fastCache.volume.*.readHits'
        ret = sp_io_rate(path, qr_128, qr_130)
        diff_time = 48540.0

        delta_spa = (1000 + 2000 + 3000 + 4000 + 5000) - (
            1000 + 1000 + 1000 + 1000 + 1000)
        expected_spa = delta_spa / diff_time
        assert_that(ret['spa'], close_to(expected_spa, 0.01))

        delta_spb = (2000 + 4000 + 6000 + 8000 + 10000) - (
            2000 + 2000 + 2000 + 2000 + 2000)
        expected_spb = delta_spb / diff_time
        assert_that(ret['spb'], close_to(expected_spb, 0.01))

    def test_sp_io_rate_error_path(self):
        def f():
            sp_io_rate(['a', 'b'], None, None)

        assert_that(f, raises(ValueError, 'takes in one and only one path.'))

    @patch_rest
    def test_byte_rate(self):
        path = ['sp.*.storage.lun.*.readBlocks',
                'sp.*.storage.blockSize']
        ret = byte_rate(path, qr_128, qr_130)

        delta_read_blocks = (10831709 - 10677980)
        block_size = 512
        diff_time = 48540.0

        expected = delta_read_blocks * block_size / diff_time
        assert_that(ret['sv_4'], close_to(expected, 0.01))

    def test_byte_rate_error_path(self):
        def f():
            byte_rate(['a', 'b', 'c'], None, None, None)

        assert_that(f, raises(ValueError,
                              'takes in "Blocks" and "blockSize" counter.'))

    @patch_rest
    def test_total_byte_rate(self):
        path = ['sp.*.physical.disk.*.readBlocks',
                'sp.*.physical.disk.*.writeBlocks',
                'sp.*.physical.blockSize']
        ret = total_byte_rate(path, qr_128, qr_130)

        delta_read_byte = (7235384336 - 7136076816) * 512 + \
                          (1348912 - 1348912) * 512
        delta_write_byte = (1000 - 10) * 512 + (1100 - 20) * 512
        diff_time = 48540.0

        expected = (delta_read_byte + delta_write_byte) / diff_time
        assert_that(ret['dae_0_1_disk_1'], close_to(expected, 0.01))

    def test_total_byte_rate_error_path(self):
        def f():
            total_byte_rate(['a', 'b', 'c', 'd'], None, None)

        msg = 'takes in "readBlocks", "writeBlocks" and "blockSize" counter.'
        assert_that(f, raises(ValueError, msg))

    @patch_rest
    def test_sp_byte_rate(self):
        path = ['sp.*.storage.summary.readBlocks',
                'sp.*.storage.blockSize']
        ret = sp_byte_rate(path, qr_128, qr_130)

        delta_blocks = 11450335 - 11289244
        block_size = 512
        diff_time = 48540.0

        expected = delta_blocks * block_size / diff_time
        assert_that(ret['spa'], close_to(expected, 0.01))

    def test_sp_byte_rate_error_path(self):
        def f():
            sp_byte_rate(['a', 'b', 'c'], None, None)

        assert_that(f, raises(ValueError,
                              'takes in "Blocks" and "blockSize" counter.'))

    @patch_rest
    def test_sp_total_byte_rate(self):
        path = ['sp.*.storage.summary.readBlocks',
                'sp.*.storage.summary.writeBlocks',
                'sp.*.storage.blockSize']
        ret = sp_total_byte_rate(path, qr_128, qr_130)

        delta_blocks_1 = 11450335 - 11289244
        delta_blocks_2 = 33497820 - 32954971
        block_size = 512
        diff_time = 48540.0

        expected = (delta_blocks_1 + delta_blocks_2) * block_size / diff_time
        assert_that(ret['spa'], close_to(expected, 0.01))

    def test_sp_total_byte_rate_error_path(self):
        def f():
            sp_total_byte_rate(['a', 'b', 'c', 'd'], None, None)

        msg = 'takes in "readBlocks", "writeBlocks" and "blockSize" counter.'
        assert_that(f, raises(ValueError, msg))

    @patch_rest
    def test_system_byte_rate(self):
        path = ['sp.*.storage.summary.readBlocks',
                'sp.*.storage.blockSize']
        ret = system_byte_rate(path, qr_128, qr_130)

        delta_bytes = (11450335 - 11289244) * 512 + (183144 - 183137) * 512
        diff_time = 48540.0

        expected = delta_bytes / diff_time
        assert_that(ret['0'], close_to(expected, 0.01))

    def test_system_byte_rate_error_path(self):
        def f():
            system_byte_rate(['a', 'b', 'c'], None, None)

        assert_that(f, raises(ValueError,
                              'takes in "Blocks" and "blockSize" counter.'))

    @patch_rest
    def test_system_total_byte_rate(self):
        path = ['sp.*.storage.summary.readBlocks',
                'sp.*.storage.summary.writeBlocks',
                'sp.*.storage.blockSize']
        ret = system_total_byte_rate(path, qr_128, qr_130)

        delta_byte_1 = ((11450335 - 11289244) + (183144 - 183137)) * 512
        delta_byte_2 = ((33497820 - 32954971) + (70507 - 70507)) * 512
        diff_time = 48540.0

        expected = (delta_byte_1 + delta_byte_2) / diff_time
        assert_that(ret['0'], close_to(expected, 0.01))

    def test_system_total_byte_rate_error_path(self):
        def f():
            system_total_byte_rate(['a', 'b', 'c', 'd'], None, None)

        msg = 'takes in "readBlocks", "writeBlocks" and "blockSize" counter.'
        assert_that(f, raises(ValueError, msg))


class UnityMetricConfigTest(TestCase):
    def test_default_calculator(self):
        mc = UnityMetricConfig({'name': 'test'})
        assert_that(mc.calculator, equal_to(calculator.delta_ps))

    def test_path_str(self):
        mc = UnityMetricConfig({'name': 'test', 'paths': 'abc'})
        assert_that(len(mc.paths), equal_to(1))
        assert_that(mc.paths, has_item('abc'))

    def test_path_collection(self):
        mc = UnityMetricConfig({'name': 'test', 'paths': ['a', 'b']})
        assert_that(mc.paths, has_items('a', 'b'))


class UnityMetricConfigParserTest(TestCase):
    config = UnityMetricConfigParser()

    def test_get_configs(self):
        disk_config = self.config.get_config('UnityDisk')
        assert_that(disk_config.metric_names(),
                    has_items('read_mbps', 'write_iops'))
