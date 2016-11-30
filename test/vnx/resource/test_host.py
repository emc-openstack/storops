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

from hamcrest import equal_to, assert_that, none, has_items, only_contains

from storops.vnx.resource.host import VNXHostList, VNXHost
from test.vnx.cli_mock import t_cli, patch_cli

__author__ = 'Cedric Zhuang'


class VNXHostTest(TestCase):
    @patch_cli
    def test_get_all(self):
        host_list = VNXHostList(t_cli())
        assert_that(len(host_list), equal_to(6))
        assert_that(host_list.name, has_items(
            'APM00152312055-spB', 'APM00152312055-spA', 'ubuntu-server11',
            'ubuntu-server7', 'Celerra_CS0_21132', 'ubuntu14'))

    @patch_cli
    def test_name_filter_of_get_all(self):
        host_list = VNXHostList(t_cli(), names=('ubuntu-server11', 'ubuntu14'))
        assert_that(len(host_list), equal_to(2))
        assert_that(host_list.name, has_items('ubuntu-server11', 'ubuntu14'))

    @patch_cli
    def test_host_property(self):
        host = VNXHost.get(cli=t_cli(), name='ubuntu-server7')
        assert_that(host.name, equal_to('ubuntu-server7'))
        assert_that(host.existed, equal_to(True))
        assert_that(len(host.connections), equal_to(15))
        assert_that(host.storage_group.name, equal_to('ubuntu-server7'))
        assert_that(len(host.lun_list), equal_to(0))

    @patch_cli
    def test_host_with_lun(self):
        host = VNXHost.get(cli=t_cli(), name='ubuntu14')
        assert_that(host.lun_list.lun_id, only_contains(4, 15))
        assert_that(host.alu_hlu_map[4], equal_to(14))
        assert_that(host.alu_hlu_map[15], equal_to(154))
        assert_that(host.alu_ids, only_contains(4, 15))
        assert_that(host.hlu_ids, only_contains(14, 154))

    @patch_cli
    def test_host_not_found(self):
        host = VNXHost.get(cli=t_cli(), name='not_found')
        assert_that(host.existed, equal_to(False))
        assert_that(host.name, equal_to('not_found'))
        assert_that(host.connections, none())
