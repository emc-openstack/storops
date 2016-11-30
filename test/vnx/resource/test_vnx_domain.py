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

from hamcrest import assert_that, equal_to, contains_string, is_not, none, \
    has_item, close_to

from storops.lib.common import instance_cache
from test.vnx.cli_mock import t_cli, patch_cli, t_vnx
from storops.vnx.enums import VNXSPEnum
from storops.vnx.resource.vnx_domain import VNXDomainNodeList, \
    VNXNetworkAdmin, VNXStorageProcessor, VNXStorageProcessorList

__author__ = 'Cedric Zhuang'


class VNXStorageProcessorTest(TestCase):
    @patch_cli
    def test_sp_list_update_without_poll(self):
        sp_list = self.get_sp_list()
        with sp_list.with_no_poll():
            sp_list.update()
        assert_that(sp_list.total_reads, has_item(1234))
        assert_that(sp_list.timestamp, is_not(none()))

    def get_sp_list(self):
        vnx = t_vnx()
        sp_list = VNXStorageProcessorList(vnx.spa, vnx.spb)
        return sp_list

    @patch_cli
    def test_default_metric_csv_filename(self):
        sp_list = self.get_sp_list()
        filename = sp_list.get_default_metric_csv_filename()
        assert_that(filename, contains_string('.storops'))
        assert_that(filename,
                    contains_string('_VNXStorageProcessor.csv'))

    @patch_cli
    def test_sp_properties(self):
        sp = VNXStorageProcessor(t_cli(), VNXSPEnum.SP_A, '1.1.1.2')
        assert_that(sp.cabinet, equal_to('DPE9'))
        assert_that(sp.signature, equal_to(4022290))
        assert_that(sp.name, equal_to('A'))
        assert_that(sp.enum, equal_to(VNXSPEnum.SP_A))

        sp = VNXStorageProcessor(t_cli(), VNXSPEnum.SP_B, '1.1.1.3')
        assert_that(sp.cabinet, equal_to('DPE9'))
        assert_that(sp.signature, equal_to(4022287))
        assert_that(sp.name, equal_to('B'))
        assert_that(sp.revision, equal_to('05.33.008.3.297'))
        assert_that(sp.serial, equal_to('FCNJT152200015'))
        assert_that(sp.memory_size, equal_to(32768))
        assert_that(sp.enum, equal_to(VNXSPEnum.SP_B))
        assert_that(sp.statistics_logging, equal_to(True))
        assert_that(sp.system_fault_led, equal_to(False))
        assert_that(sp.read_cache_enabled, equal_to(True))
        assert_that(sp.write_cache_enabled, equal_to(True))
        assert_that(sp.max_requests, none())
        assert_that(sp.average_requests, none())
        assert_that(sp.hard_errors, none())
        assert_that(sp.total_reads, equal_to(7978))
        assert_that(sp.total_writes, equal_to(6364257))
        assert_that(sp.prct_busy, equal_to(1.91))
        assert_that(sp.prct_idle, equal_to(98.0))
        assert_that(str(sp.system_timestamp), equal_to('2016-04-26 09:59:16'))
        assert_that(sp.day_of_the_week, equal_to('Tuesday'))
        assert_that(sp.read_requests, equal_to(8308))
        assert_that(sp.write_requests, equal_to(6364593))
        assert_that(sp.blocks_read, equal_to(975038))
        assert_that(sp.blocks_written, equal_to(199037219))
        assert_that(sp.sum_queue_lengths_by_arrivals, equal_to(8059572))
        assert_that(sp.arrivals_to_non_zero_queue, equal_to(1321389))
        assert_that(sp.hw_flush_on, equal_to(False))
        assert_that(sp.idle_flush_on, equal_to(False))
        assert_that(sp.lw_flush_off, equal_to(False))
        assert_that(sp.write_cache_flushes, equal_to(468636))
        assert_that(sp.write_cache_blocks_flushed, equal_to(477297069))
        assert_that(sp.controller_busy_ticks, equal_to(46703))
        assert_that(sp.controller_idle_ticks, equal_to(2394689))

    @property
    @instance_cache
    def sp_a(self):
        return VNXStorageProcessor(t_cli(), VNXSPEnum.SP_A, '10.244.211.30')

    @patch_cli
    def test_sp_read_iops(self):
        assert_that(self.sp_a.read_iops, equal_to(5.5))

    @patch_cli
    def test_sp_write_iops(self):
        assert_that(self.sp_a.write_iops, equal_to(5.6))

    @patch_cli
    def test_sp_total_iops(self):
        assert_that(self.sp_a.total_iops, equal_to(11.1))

    @patch_cli
    def test_sp_read_mbps(self):
        assert_that(self.sp_a.read_mbps, equal_to(5.8))

    @patch_cli
    def test_sp_write_mbps(self):
        assert_that(self.sp_a.write_mbps, equal_to(5.9))

    @patch_cli
    def test_sp_total_mbps(self):
        assert_that(self.sp_a.total_mbps, equal_to(11.7))

    @patch_cli
    def test_sp_read_size_kb(self):
        assert_that(self.sp_a.read_size_kb, close_to(1079.8, 0.1))

    @patch_cli
    def test_sp_write_size_kb(self):
        assert_that(self.sp_a.write_size_kb, close_to(1078.8, 0.1))


class VNXDomainNodeListTest(TestCase):
    @patch_cli
    def setUp(self):
        self.dnl = VNXDomainNodeList(t_cli())

    @patch_cli
    def test_iterable(self):
        assert_that(len(self.dnl), equal_to(2))

    @patch_cli
    def test_get_node(self):
        node = self.dnl.get_node('APM00153906536')
        assert_that(len(node.members), equal_to(2))

    @patch_cli
    def test_get_node_not_found(self):
        assert_that(self.dnl.get_node('abcde'), none())

    @patch_cli
    def test_get_spa_check_ip(self):
        node = self.dnl.get_node('APM00152904560')
        assert_that(node.spa.ip, equal_to('192.168.1.94'))
        assert_that(node.spb.ip, equal_to('192.168.1.95'))
        assert_that(node.control_station.ip, equal_to('192.168.1.93'))

    @patch_cli
    def test_get_cs_ip(self):
        assert_that(VNXDomainNodeList.get_cs_ip('APM00153042305', t_cli()),
                    equal_to('10.244.211.32'))


class VNXDomainMemberListTest(TestCase):
    @patch_cli(output='domain_-list_normal.txt')
    def setUp(self):
        dnl = VNXDomainNodeList(t_cli())
        self.dml = dnl[0].members

    @patch_cli
    def test_iterable(self):
        count = 0
        for _ in self.dml:
            count += 1
        assert_that(count, equal_to(3))

    @patch_cli
    def test_properties(self):
        str_value = str(self.dml)
        assert_that(str_value, contains_string('VNXDomainMember'))
        assert_that(str_value, contains_string('VNXDomainMemberList'))
        assert_that(str_value, is_not(contains_string('::')))

    @patch_cli
    def test_sp(self):
        spa = self.dml.spa
        assert_that(spa.ip, equal_to('10.244.211.30'))
        assert_that(spa.is_master, equal_to(True))
        spb = self.dml.spb
        assert_that(spb.ip, equal_to('10.244.211.31'))
        assert_that(spb.is_master, equal_to(False))
        cs = self.dml.control_station
        assert_that(cs.ip, equal_to('10.244.211.32'))


class VNXNetworkAdminTest(TestCase):
    @patch_cli
    def test_properties(self):
        sp = VNXNetworkAdmin(VNXSPEnum.SP_A, t_cli())
        with sp.with_no_poll():
            assert_that(sp.name, equal_to('vnx2_1_52'))
            assert_that(sp.sp, equal_to(VNXSPEnum.SP_A))
            assert_that(sp.link_status, equal_to('Link-Up'))
            assert_that(sp.subnet_mask, equal_to('255.255.255.0'))
            assert_that(sp.ip, equal_to('192.168.1.52'))
            assert_that(sp.ip_mode, equal_to('Manual'))
            assert_that(sp.gateway, equal_to('192.168.1.1'))
            assert_that(sp.virtual_port_id, equal_to(0))
            assert_that(sp.ipv6_enabled, equal_to(False))
            assert_that(sp.port_id, equal_to(0))
            assert_that(sp.vlan_id, equal_to(None))

    @patch_cli
    def test_get_spa_ip(self):
        assert_that(VNXNetworkAdmin.get_spa_ip(t_cli()),
                    equal_to('192.168.1.52'))

    @patch_cli
    def test_get_spb_ip(self):
        assert_that(VNXNetworkAdmin.get_spb_ip(t_cli()),
                    equal_to('192.168.1.53'))
