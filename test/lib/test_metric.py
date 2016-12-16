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
import unittest
from time import sleep

from hamcrest import assert_that, less_than, greater_than, none, equal_to, \
    has_items, contains_string

from storops.lib.common import get_data_file
from storops.lib.metric import PerfManager, MetricCounterRecords, MetricsDumper
from storops.unity.resource.disk import UnityDiskList, UnityDisk
from storops.unity.resource.lun import UnityLun, UnityLunList

__author__ = 'Cedric Zhuang'


class PerfManagerTest(unittest.TestCase):
    def perf_mon(self):
        return PerfManager()

    def test_enable_perf_metric(self):
        cli = self.perf_mon()
        assert_that(cli.is_perf_metric_enabled(), equal_to(False))
        cli.enable_perf_metric(0, lambda: 1)
        assert_that(cli.is_perf_metric_enabled(), equal_to(True))
        cli.disable_perf_metric()
        assert_that(cli.is_perf_metric_enabled(), equal_to(False))

    def test_double_enable(self):
        cli = self.perf_mon()
        c = []
        cli.enable_perf_metric(0.1, lambda: c.append(1))
        sleep(0.5)
        assert_that(len(c), greater_than(1))
        assert_that(len(c), less_than(8))
        cli.enable_perf_metric(10, lambda: c.append(1))
        sleep(0.5)
        assert_that(len(c), less_than(10))
        cli.disable_perf_metric()
        assert_that(cli.prev_counter, none())
        assert_that(cli.curr_counter, none())
        assert_that(cli.is_perf_metric_enabled(), equal_to(False))

    def test_is_perf_metric_enabled_rsc_default(self):
        cli = self.perf_mon()
        cli.enable_perf_metric(0, lambda: 1)
        enabled = cli.is_perf_metric_enabled(UnityDiskList(cli=cli))
        assert_that(enabled, equal_to(True))
        enabled = cli.is_perf_metric_enabled(UnityDisk(_id='', cli=cli))
        assert_that(enabled, equal_to(True))

    def test_is_perf_metric_enabled_rsc_specific(self):
        cli = self.perf_mon()
        cli.enable_perf_metric(0, lambda: 1, [UnityDisk])
        enabled = cli.is_perf_metric_enabled(UnityDiskList(cli=cli))
        assert_that(enabled, equal_to(True))

        enabled = cli.is_perf_metric_enabled(UnityLunList(cli=cli))
        assert_that(enabled, equal_to(False))

        enabled = cli.is_perf_metric_enabled(UnityDisk(_id='', cli=cli))
        assert_that(enabled, equal_to(True))

        enabled = cli.is_perf_metric_enabled(UnityLun(_id='', cli=cli))
        assert_that(enabled, equal_to(False))

    def test_is_perf_monitored_default(self):
        assert_that(self.perf_mon()._is_perf_monitored('abc'), equal_to(True))

    def test_is_perf_monitored_resource(self):
        cli = self.perf_mon()
        cli._rsc_clz_list = [UnityDisk]
        assert_that(cli._is_perf_monitored(UnityDisk('', cli=cli)),
                    equal_to(True))
        assert_that(cli._is_perf_monitored(UnityLun('', cli=cli)),
                    equal_to(False))

    def test_is_perf_monitored_resource_list(self):
        cli = self.perf_mon()
        cli._rsc_clz_list = [UnityDisk]
        assert_that(cli._is_perf_monitored(UnityDiskList(cli=cli)),
                    equal_to(True))
        assert_that(cli._is_perf_monitored(UnityLunList(cli=cli)),
                    equal_to(False))


class MetricCounterRecordsTest(unittest.TestCase):
    def test_max_count(self):
        records = MetricCounterRecords()
        records.add_results(1)
        records.add_results(2)
        records.add_results(3)
        assert_that(len(records), equal_to(2))
        assert_that(records._records, has_items(2, 3))
        assert_that(records.enabled, equal_to(True))

    def test_default_enabled(self):
        records = MetricCounterRecords()
        assert_that(records.enabled, equal_to(False))

    def test_reset(self):
        records = MetricCounterRecords()
        records.add_results(1)
        records.reset()
        assert_that(len(records), equal_to(0))
        assert_that(records.enabled, equal_to(False))

    def test_add_none_result(self):
        records = MetricCounterRecords()
        records.add_results(None)
        assert_that(len(records), equal_to(0))

    def test_curr_prev_value(self):
        records = MetricCounterRecords()
        assert_that(records.curr, none())
        assert_that(records.prev, none())

        records.add_results(1)
        assert_that(records.curr, equal_to(1))
        assert_that(records.prev, none())

        records.add_results(2)
        assert_that(records.curr, equal_to(2))
        assert_that(records.prev, equal_to(1))

        records.add_results(3)
        assert_that(records.curr, equal_to(3))
        assert_that(records.prev, equal_to(2))

        records.enabled = False
        assert_that(records.curr, none())
        assert_that(records.prev, none())


class SampleRscList(object):
    def __init__(self):
        self.list = [{'time': 1, 'name': 'a', 'ma': 1, 'mb': 2.0, 'mc': 'aaa'},
                     {'time': 1, 'name': 'b', 'ma': 4, 'mb': 5.0, 'mc': 'bbb'}]

    @staticmethod
    def metric_names():
        return ['ma', 'mb', 'mc']

    def __iter__(self):
        return self.list.__iter__()

    @staticmethod
    def _hdr_cb(rsc):
        return list(map(str, [rsc['time'], rsc['name']]))


class MetricsDumperTest(unittest.TestCase):
    dumper = MetricsDumper(SampleRscList(), ['time', 'name'],
                           SampleRscList._hdr_cb)
    filename = get_data_file('temp_test_metric.csv')

    @classmethod
    def tearDownClass(cls):
        # noinspection PyBroadException
        try:
            os.remove(cls.filename)
        except Exception:
            pass

    def test_metric_names(self):
        assert_that(self.dumper.metric_names, has_items('ma', 'mb', 'mc'))

    def test_get_metrics_csv_header(self):
        assert_that(self.dumper.get_metrics_csv_header(),
                    equal_to('time,name,ma,mb,mc'))

    def test_get_metrics_csv_data(self):
        data = self.dumper.get_metrics_csv_data()
        assert_that(data, contains_string('1,a,1,2.0,aaa'))
        assert_that(data, contains_string('1,b,4,5.0,bbb'))

    def test_data_line(self):
        assert_that(self.dumper.data_line(next(iter(SampleRscList()))),
                    has_items('1', 'a', '1', '2.0', 'aaa'))

    def test_persist_metric_data(self):
        filename = self.filename
        self.dumper.persist_metric_data(filename)
        exists = os.path.exists(filename)
        assert_that(exists, equal_to(True), '{} not found.'.format(filename))
