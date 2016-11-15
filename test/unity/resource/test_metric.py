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

from hamcrest import assert_that, equal_to, has_items, raises, instance_of

from storops import MetricTypeEnum
from storops.exception import UnityMetricQueryNotFoundError
from storops.unity.calculator import IdValues
from storops.unity.resource.metric import UnityMetric, UnityMetricList, \
    UnityMetricRealTimeQuery, UnityMetricRealTimeQueryList
from test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


@patch_rest
def get_query_result(query_id, paths=None):
    return UnityMetricRealTimeQuery(
        cli=t_rest(), _id=query_id).get_query_result(paths)


qr_6 = get_query_result(6)
qr_14 = get_query_result(14)
qr_17 = get_query_result(17)
qr_34 = get_query_result(34)


class UnityMetricTest(TestCase):
    def verify_metric_10234(self, metric):
        assert_that(metric.id, equal_to(10234))
        assert_that(metric.is_historical_available, equal_to(False))
        assert_that(metric.is_realtime_available, equal_to(True))
        assert_that(metric.name, equal_to('Block Cache Clean Pages'))
        assert_that(metric.type, equal_to(MetricTypeEnum.FACT))
        assert_that(metric.unit_display_string, equal_to('Count'))
        assert_that(metric.path,
                    equal_to('sp.*.blockCache.global.summary.cleanPages'))

    def verify_metric_14732(self, metric):
        assert_that(metric.id, equal_to(14732))
        assert_that(metric.is_historical_available, equal_to(False))
        assert_that(metric.is_realtime_available, equal_to(True))
        assert_that(metric.name, equal_to('Total Scan'))
        assert_that(metric.type, equal_to(MetricTypeEnum.COUNTER_64))
        assert_that(metric.unit_display_string, equal_to('Requests'))
        assert_that(metric.description,
                    equal_to('Total number of antivirus requests'))
        assert_that(metric.path,
                    equal_to('sp.*.virusChecker.request.requests'))

    @patch_rest
    def test_get_properties(self):
        metric = UnityMetric(_id=10234, cli=t_rest())
        self.verify_metric_10234(metric)

    @patch_rest
    def test_get_all(self):
        metrics = UnityMetricList(cli=t_rest())
        assert_that(len(metrics), equal_to(2411))
        self.verify_metric_14732(*filter(lambda m: m.id == 14732, metrics))
        self.verify_metric_10234(*filter(lambda m: m.id == 10234, metrics))


class UnityMetricRealTimeQueryTest(TestCase):
    @patch_rest
    def test_create_query(self):
        paths = ['sp.*.physical.disk.*.reads', 'sp.*.physical.disk.*.writes']
        query = UnityMetricRealTimeQuery.create(t_rest(), 30, paths)
        assert_that(query.paths, has_items(*paths))

    @patch_rest
    def test_delete_query(self):
        def f():
            query = UnityMetricRealTimeQuery(_id=4, cli=t_rest())
            query.delete()

        assert_that(f, raises(UnityMetricQueryNotFoundError, 'ID not found'))

    @patch_rest
    def test_properties(self):
        query = UnityMetricRealTimeQuery(_id=2, cli=t_rest())
        self.verify_query_2(query)

    @patch_rest
    def test_get_all(self):
        query_list = UnityMetricRealTimeQueryList(cli=t_rest())
        assert_that(len(query_list), equal_to(4))
        self.verify_query_2(query_list[0])

    def verify_query_2(self, query):
        assert_that(query.id, equal_to(2))
        assert_that(query.interval, equal_to(300))
        assert_that(query.expiration.minute, equal_to(30))
        assert_that(query.paths,
                    has_items('sp.*.physical.disk.*.reads',
                              'sp.*.storage.lun.*.busyTime'))

    @patch_rest
    def test_sort_by_path(self):
        query_list = UnityMetricRealTimeQueryList(cli=t_rest())
        query_list.sort_by_path()
        assert_that(list(map(len, query_list.paths)),
                    equal_to([89, 88, 20, 1]))

    @patch_rest
    def test_all_filter_by_id(self):
        query_list = UnityMetricRealTimeQueryList(
            cli=t_rest(), id_list=[17, 22])
        assert_that(query_list.id, equal_to([17, 22]))

    @patch_rest
    def test_set_id_list(self):
        query_list = UnityMetricRealTimeQueryList(cli=t_rest())
        assert_that(len(query_list), equal_to(4))
        ret = query_list.set_id_list([17, 22])
        assert_that(ret, instance_of(UnityMetricRealTimeQueryList))
        assert_that(len(query_list), equal_to(2))

    @patch_rest
    def test_get_query_found_in_one(self):
        paths = ['sp.*.storage.lun.*.reads',
                 'sp.*.storage.lun.*.writes',
                 'sp.*.blockCache.global.summary.dirtyBytes']
        queries = UnityMetricRealTimeQuery.get_query_list(t_rest(), 300, paths)
        assert_that(len(queries), equal_to(1))
        assert_that(queries[0].paths, has_items(*paths))

    @patch_rest
    def test_get_query_found_in_two(self):
        paths = ['sp.*.blockCache.global.summary.dirtyBytes',
                 'sp.*.platform.storageProcessorTemperature']
        queries = UnityMetricRealTimeQuery.get_query_list(t_rest(), 300, paths)
        assert_that(len(queries), equal_to(2))

    @patch_rest
    def test_get_query_create_one(self):
        paths = ['sp.*.blockCache.global.summary.dirtyBytes',
                 'sp.*.platform.storageProcessorTemperature',
                 'sp.*.store.scsiBusDevice.*.calls']

        queries = UnityMetricRealTimeQuery.get_query_list(t_rest(), 300, paths)
        assert_that(len(queries._id_list), equal_to(3))

    @patch_rest
    def test_get_query_result_all(self):
        queries = UnityMetricRealTimeQueryList(cli=t_rest(), interval=300)
        assert_that(len(queries), equal_to(2))
        assert_that(len(queries.get_query_result()), equal_to(90))

    @patch_rest
    def test_get_query_result_filter_by_path(self):
        queries = UnityMetricRealTimeQueryList(cli=t_rest(), interval=300)
        paths = ['sp.*.blockCache.global.summary.dirtyBytes',
                 'sp.*.fibreChannel.blockSize',
                 'sp.*.storage.vvol.file.*.writes',
                 'not.found']
        assert_that(len(queries.get_query_result(paths)), equal_to(3))


class UnityMetricQueryResultTest(TestCase):
    def verify_disk_reads_value(self, result):
        assert_that(result.path, equal_to('sp.*.physical.disk.*.reads'))
        assert_that(result.query_id, equal_to(6))
        assert_that(result.timestamp.minute, equal_to(30))
        assert_that(len(result.values), equal_to(2))

        spa_values = result.values['spa']
        assert_that(len(spa_values), equal_to(26))

    @patch_rest
    def test_get_query_result_all(self):
        results = qr_6
        assert_that(len(results), equal_to(2))

        self.verify_disk_reads_value(
            results.by_path('sp.*.physical.disk.*.reads'))

    @patch_rest
    def test_get_query_result_filtered(self):
        paths = ['sp.*.blockCache.global.summary.dirtyBytes',
                 'sp.*.fibreChannel.blockSize',
                 'sp.*.nfs.v2.op.*.failures']
        results = get_query_result(3, paths)
        assert_that(len(results), equal_to(3))
        assert_that(results.path, has_items(*paths))

    @patch_rest
    def test_sum_sp(self):
        result = qr_6.by_path('sp.*.physical.disk.*.reads')
        sum_sp = result.sum_sp()
        assert_that(len(sum_sp), equal_to(26))
        assert_that(sum_sp['dpe_disk_8'], equal_to(122362))
        assert_that(sum_sp['dpe_disk_1'], equal_to(839944))

    @patch_rest
    def test_diff_seconds(self):
        assert_that(qr_14.diff_seconds(qr_6), equal_to(163800.0))

    @patch_rest
    def test_merge_result_list(self):
        r1 = get_query_result(18)
        r2 = get_query_result(19)
        assert_that(len(r1), equal_to(4))
        assert_that(len(r2), equal_to(3))
        r1.merge(r2)
        assert_that(len(r1), equal_to(6))

    @patch_rest
    def test_sp_values(self):
        result = qr_34.by_path('sp.*.cifs.smb1.basic.writes')
        assert_that(result.sp_values, instance_of(IdValues))
        assert_that(result.sp_values['spa'], equal_to(500))
