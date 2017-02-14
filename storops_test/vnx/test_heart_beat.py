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

import time
from hamcrest import assert_that, equal_to, ends_with, contains_string, \
    greater_than, less_than_or_equal_to, greater_than_or_equal_to, raises, \
    has_items

from storops_test.vnx.cli_mock import patch_cli
from storops.exception import VNXSystemDownError, VNXCredentialError
from storops.vnx.heart_beat import NodeInfo, NodeHeartBeat

__author__ = 'Cedric Zhuang'


class NodeHeartBeatTest(TestCase):
    def get_test_hb(self):
        hb = NodeHeartBeat(interval=0)
        hb.add('spa', '1.1.1.1')
        hb.add('spb', '1.1.1.2')
        return hb

    @patch_cli
    def test_normal(self):
        hb = NodeHeartBeat(interval=0.2)
        hb.add('spa', '1.1.1.1')
        hb.add('spb', '1.1.1.2')
        assert_that(hb.is_available('spa'), equal_to(True))
        assert_that(hb.is_available('spb'), equal_to(True))
        time.sleep(0.5)
        assert_that(hb.is_available('spa'), equal_to(True))
        assert_that(hb.is_available('spb'), equal_to(True))
        hb.stop()
        time.sleep(0.5)

    def test_add(self):
        hb = NodeHeartBeat(interval=0)
        hb.add('spa', '1.1.1.1')
        hb.add('cs', None)
        assert_that(hb.is_available('cs'), equal_to(False))

    def test_remove_extra_quotes(self):
        info = NodeInfo('spa', '  \'"1.1.1.1" \'   ')
        assert_that(info.ip, equal_to('1.1.1.1'))

    def test_is_updated_within(self):
        info = NodeInfo('spa', '1.1.1.1')
        info.available = True
        assert_that(info.is_updated_within(0), equal_to(False))
        assert_that(info.is_updated_within(1), equal_to(True))

    @patch_cli
    def test_get_alive_sp_ip(self):
        hb = NodeHeartBeat(interval=0)
        hb.add('spa', '1.1.1.1', False)
        hb.add('spb', '1.1.1.2', True)
        assert_that(hb.get_alive_sp_ip(), equal_to('1.1.1.2'))

    @patch_cli
    def test_get_alive_sp_ip_none(self):
        hb = NodeHeartBeat(interval=0)
        hb.add('spa', '1.1.1.1', False, working=False)
        hb.add('spb', '1.1.1.2', None, working=True)
        assert_that(hb.get_alive_sp_ip(), '1.1.1.2')

    @patch_cli
    def test_get_alive_sp_ip_down(self):
        def f():
            hb = NodeHeartBeat(interval=0)
            hb.add('spa', '1.1.1.1', False)
            hb.add('spb', '1.1.1.2', False)
            hb.get_alive_sp_ip()

        assert_that(f, raises(VNXSystemDownError,
                              'no storage processor available'))

    @patch_cli
    def test_get_alive_sp_ip_no_load_balance(self):
        hb = NodeHeartBeat(interval=0)
        hb.add('spa', '1.1.1.1', True, True)
        hb.add('spb', '1.1.1.2', True, False)
        assert_that(hb.get_alive_sp_ip(), equal_to('1.1.1.1'))

    @patch_cli
    def test_update_by_ip(self):
        hb = NodeHeartBeat(interval=0)
        hb.add('spa', '1.1.1.1', False)
        hb.add('spb', '1.1.1.2', False)
        hb.update_by_ip('1.1.1.1', True)
        assert_that(hb.get_alive_sp_ip(), equal_to('1.1.1.1'))

    @patch_cli
    def test_update_by_ip_latency(self):
        hb = NodeHeartBeat(interval=0.01)
        hb.add('spa', '1.1.1.1', False)
        node = hb.nodes[0]
        assert_that(node.available, equal_to(False))
        time.sleep(0.06)
        assert_that(node.available, equal_to(True))
        assert_that(hb.command_count, greater_than(1))
        hb.stop()
        time.sleep(0.06)

    @patch_cli
    def test_interval_change(self):
        hb = NodeHeartBeat(interval=0.1)
        hb.add('spa', '1.1.1.1')
        hb.add('spb', '1.1.1.2')
        time.sleep(0.6)
        hb.interval = 2
        time.sleep(1)
        # total call count is calculated like this:
        #   interval = 0.1, duration = 0.5, 5 >= cycle >= 4
        #   interval = 2, duration = 1, 0 <= cycle <= 1
        #   4 <= total cycle <= 6
        # each cycle has 2 call (one for each SP)
        # 8 <= total call count <= 12
        assert_that(hb.command_count, less_than_or_equal_to(12))
        assert_that(hb.command_count, greater_than_or_equal_to(4))
        hb.stop()
        time.sleep(1)

    @patch_cli
    def test_interval_no_loop(self):
        hb = self.get_test_hb()
        assert_that(hb.command_count, equal_to(0))
        hb.interval = 1
        time.sleep(0.2)
        assert_that(hb.command_count, greater_than(0))

    @patch_cli
    def test_repr(self):
        hb = self.get_test_hb()
        string = repr(hb)
        assert_that(string, contains_string('node count: 2'))

    def test_ping_sp_cmd(self):
        hb = NodeHeartBeat(interval=20)
        ip = '1.1.1.1'
        hb.add('spa', ip)
        hb.update_by_ip(ip, latency=5.123)
        assert_that(' '.join(hb.get_agent(ip)),
                    ends_with('-h 1.1.1.1 -t 35 -np getagent'))
        hb.stop()

    def test_is_all_sps_alive(self):
        hb = self.get_test_hb()
        assert_that(hb.is_all_sps_alive(), equal_to(True))
        hb.update_by_ip('1.1.1.1', available=False)
        assert_that(hb.is_all_sps_alive(), equal_to(False))

    def test_get_all_alive_sps_ip(self):
        hb = self.get_test_hb()
        assert_that(hb.get_all_alive_sps_ip(),
                    has_items('1.1.1.1', '1.1.1.2'))

    @patch_cli(output='credential_error.txt')
    def test_execute_cmd_credential_error(self):
        hb = self.get_test_hb()
        try:
            hb.execute_cmd(
                '1.1.1.1',
                ['naviseccli', '-h', '1.1.1.1', 'getagent'])
        except VNXCredentialError:
            pass
        assert_that(hb.is_credential_valid, equal_to(False))

    @patch_cli(output='ip_error.txt')
    def test_execute_cmd_ip_error(self):
        def f():
            hb = self.get_test_hb()
            hb.execute_cmd('abc', ['naviseccli', '-h', 'abc', 'getagent'])

        assert_that(f, raises(VNXCredentialError, 'not connect to'))

    @patch_cli(output='credential_error.txt')
    def test_credential_error_no_heart_beat(self):
        hb = NodeHeartBeat(interval=0.01)
        hb.add('spa', '1.1.1.1')
        hb.add('spb', '1.1.1.2')
        assert_that(hb.is_available('spa'), equal_to(True))
        assert_that(hb.is_available('spb'), equal_to(True))
        time.sleep(0.1)
        assert_that(hb.command_count, less_than_or_equal_to(2))
        assert_that(hb.command_count, less_than_or_equal_to(2))
        hb.stop()
        time.sleep(0.1)


class NodeInfoTest(TestCase):
    def test_repr(self):
        info = NodeInfo('spa', '1.1.1.1', True, False)
        info.latency = 5
        info.latency = 14
        expected = ('name: SP A, ip: 1.1.1.1, available: True, '
                    'working: False, latency: 10.0, timestamp: None')
        assert_that(repr(info), equal_to(expected))
