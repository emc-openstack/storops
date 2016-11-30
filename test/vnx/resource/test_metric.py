# coding=utf-8
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

from hamcrest import assert_that, equal_to, none

from storops.vnx.resource.metric import VNXStats
from test.vnx.cli_mock import t_cli, patch_cli

__author__ = 'Cedric Zhuang'


class VNXStatsTest(TestCase):
    stats = VNXStats.get(t_cli())

    @patch_cli
    def test_get_stats_status_disabled(self):
        assert_that(self.stats.is_enabled(), equal_to(False))

    @patch_cli(output='setstats_enabled.txt')
    def test_get_stats_status_enabled(self):
        assert_that(self.stats.is_enabled(), equal_to(True))

    @patch_cli
    def test_enable_stats(self):
        assert_that(self.stats.enable_stats(), none())

    @patch_cli
    def test_disable_stats(self):
        assert_that(self.stats.disable_stats(), none())
