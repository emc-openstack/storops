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

from hamcrest import assert_that, has_items, equal_to, raises, has_item, \
    close_to, is_not

from storops.unity import calculator
from storops.unity.calculator import calculators, IdValues, \
    delta_ps, mb_ps_by_block, busy_idle_util, \
    sp_delta_ps, sp_mb_ps_by_byte, sp_mb_ps_by_block, sp_busy_idle_util, \
    only_one_path, sp_fact, all_not_none, UnityMetricConfig, \
    UnityMetricConfigParser
from storops.unity.resource.disk import UnityDisk
from storops.unity.resource.filesystem import UnityFileSystem
from test.unity.resource.test_metric import qr_6, qr_14, qr_17, qr_34
from test.unity.rest_mock import patch_rest
from test.utils import is_nan

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
