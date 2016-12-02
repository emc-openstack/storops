# Copyright (c) 2016 EMC Corporation.
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

from hamcrest import assert_that, instance_of, equal_to

from storops.vnx.calculator import VNXMetricConfigParser, VNXMetricConfig, \
    VNXMetricConfigList, minus, div, round_60
from storops.vnx.resource.lun import VNXLun
from test.utils import is_nan

__author__ = 'Cedric Zhuang'


class MathOperationsTest(TestCase):
    def test_minus_op1_none(self):
        assert_that(minus(None, 5.0), is_nan())

    def test_minus_op2_none(self):
        assert_that(minus(1, None), is_nan())

    def test_minus_normal(self):
        assert_that(minus(32, 50.0), equal_to(-18.0))

    def test_minus_nan(self):
        assert_that(minus(float('nan'), 5.0), is_nan())

    def test_div_op1_none(self):
        assert_that(div(None, 5.0), is_nan())

    def test_div_op2_none(self):
        assert_that(div(3, None), is_nan())

    def test_div_op2_zero(self):
        assert_that(div(4, 0), is_nan())

    def test_div_nan(self):
        assert_that(div(float('nan'), 4.2), is_nan())

    def test_div_normal(self):
        assert_that(div(6, 2.0), equal_to(3.0))

    def test_round_60_higher_half(self):
        assert_that(round_60(113.5), equal_to(120))

    def test_round_60_lower_half(self):
        assert_that(round_60(132.3), equal_to(120))

    def test_round_60_nan(self):
        assert_that(round_60(float('nan')), is_nan())

    def test_round_60_none(self):
        assert_that(round_60(None), is_nan())


class VNXMetricConfigCalculatorTest(TestCase):
    def test_get_config(self):
        config = VNXMetricConfigParser.get_config(VNXLun)
        assert_that(config, instance_of(VNXMetricConfigList))

    def test_get_metric_config(self):
        config = VNXMetricConfigParser.get_config(VNXLun)
        metric_config = config.get_metric_config('read_iops')
        assert_that(metric_config, instance_of(VNXMetricConfig))
        assert_that(metric_config.name, equal_to('read_iops'))
