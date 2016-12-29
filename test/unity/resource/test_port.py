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

import ddt
from hamcrest import assert_that, equal_to, instance_of, only_contains, \
    raises, contains_string
from storops.exception import UnityEthernetPortSpeedNotSupportError, \
    UnityEthernetPortMtuSizeNotSupportError, UnityResourceNotFoundError, \
    UnityPolicyNameInUseError, UnityEthernetPortAlreadyAggregatedError
from storops.exception import SystemAPINotSupported
from storops.unity.enums import ConnectorTypeEnum, EPSpeedValuesEnum, \
    FcSpeedEnum, IOLimitPolicyStateEnum
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.port import UnityEthernetPort, \
    UnityEthernetPortList, UnityIpPort, UnityIpPortList, UnityIscsiPortal, \
    UnityIscsiPortalList, UnityIscsiNode, UnityFcPort, UnityFcPortList, \
    UnityIoLimitRule, UnityIoLimitPolicy, UnityIoLimitPolicyList, \
    UnityLinkAggregation
from storops.unity.resource.sp import UnityStorageProcessor
from test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityIpPortTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        port = UnityIpPort('spa_eth2', cli=t_rest())
        assert_that(port.name, equal_to('SP A Ethernet Port 2'))
        assert_that(port.short_name, equal_to('Ethernet Port 2'))
        assert_that(port.sp, instance_of(UnityStorageProcessor))
        assert_that(port.is_link_up, equal_to(True))
        assert_that(port.mac_address, equal_to('00:60:16:5C:08:E1'))

    @patch_rest
    def test_get_all(self):
        ports = UnityIpPortList(cli=t_rest())
        assert_that(len(ports), equal_to(8))

    @patch_rest
    def test_is_link_aggregation(self):
        port = UnityIpPort('spa_eth3', cli=t_rest())
        assert_that(port.is_link_aggregation(), equal_to(False))
        port = UnityIpPort('spa_la_2', cli=t_rest())
        assert_that(port.is_link_aggregation(), equal_to(True))

    @patch_rest
    def test_is_link_aggregation_not_supported(self):
        port = UnityIpPort('spa_eth6', cli=t_rest("4.0"))
        assert_that(port.is_link_aggregation(), equal_to(False))

    @patch_rest
    def test_set_mtu_on_eth_port(self):
        port = UnityIpPort('spa_eth3', cli=t_rest())
        port.set_mtu(1500)

    @patch_rest
    def test_set_mtu_on_link_aggregation(self):
        la = UnityIpPort('spa_la_2', cli=t_rest())
        la.set_mtu(1500)

    @patch_rest
    def test_mtu_of_link_aggregation(self):
        la = UnityIpPort('spa_la_2', cli=t_rest())
        assert_that(la.mtu, equal_to(9000))

    @patch_rest
    def test_mtu_of_eth_port(self):
        port = UnityIpPort('spa_eth3', cli=t_rest())
        assert_that(port.mtu, equal_to(1500))


@ddt.ddt
class UnityEthernetPortTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        port = UnityEthernetPort('spa_eth3', cli=t_rest())
        assert_that(port.name, equal_to('SP A Ethernet Port 3'))
        assert_that(port.mac_address, equal_to("00:60:16:5C:07:0A"))
        assert_that(port.parent_storage_processor, equal_to(
            UnityStorageProcessor('spa', cli=t_rest())))
        assert_that(port.mtu, equal_to(1500))
        assert_that(port.requested_mtu, equal_to(1500))
        assert_that(port.connector_type, equal_to(ConnectorTypeEnum.RJ45))
        assert_that(port.supported_speeds, only_contains(
            EPSpeedValuesEnum.AUTO,
            EPSpeedValuesEnum._100MbPS,
            EPSpeedValuesEnum._1GbPS,
            EPSpeedValuesEnum._10GbPS))
        assert_that(port.supported_mtus, only_contains(1500, 9000))
        assert_that(port.speed, equal_to(None))
        assert_that(port.needs_replacement, equal_to(False))
        assert_that(port.is_link_up, equal_to(False))
        assert_that(port.bond, equal_to(False))

    @patch_rest
    def test_modify_mtu(self):
        port = UnityEthernetPort(cli=t_rest(), _id='spa_eth3')
        port.modify(mtu=9000)

    @patch_rest
    def test_modify_mtu_to_invalid_value(self):
        def do():
            port = UnityEthernetPort(cli=t_rest(), _id='spb_eth3')
            port.modify(mtu=10000)

        assert_that(do, raises(UnityEthernetPortMtuSizeNotSupportError))

    @patch_rest
    def test_modify_mtu_to_same_value(self):
        port = UnityEthernetPort(cli=t_rest(), _id='spb_eth3')
        port.modify(mtu=1500)

    @patch_rest
    def test_modify_speed(self):
        port = UnityEthernetPort(cli=t_rest(), _id='spa_eth3')
        port.modify(speed=100)

    @patch_rest
    def test_modify_speed_to_same_value(self):
        port = UnityEthernetPort(cli=t_rest(), _id='spb_eth3')
        port.modify(speed=EPSpeedValuesEnum.AUTO)

    @patch_rest
    def test_modify_speed_to_invalid_value(self):
        def do():
            port = UnityEthernetPort(cli=t_rest(), _id='spb_eth3')
            port.modify(speed=40000)

        assert_that(do, raises(UnityEthernetPortSpeedNotSupportError))

    @patch_rest
    def test_modify_when_peer_not_exist(self):
        port = UnityEthernetPort(cli=t_rest(), _id='spa_eth4')
        port.modify(mtu=1500)

    @ddt.data({'port_id': 'spa_eth2',
               'peer_id': 'spb_eth2'},
              {'port_id': 'spb_eth3',
               'peer_id': 'spa_eth3'})
    @ddt.unpack
    def test_get_peer(self, port_id, peer_id):
        port = UnityEthernetPort(cli=t_rest(), _id=port_id)
        peer = port.get_peer()
        assert_that(peer.get_id(), equal_to(peer_id))


class UnityEthernetPortListTest(TestCase):
    @patch_rest
    def test_filter(self):
        port_id = 'spa_eth2'

        all_ports = UnityEthernetPortList(cli=t_rest())
        ports = all_ports.shadow_copy(port_ids=[port_id])
        assert_that(len(ports), equal_to(1))
        assert_that(ports[0].get_id(), equal_to(port_id))

        ports = UnityEthernetPortList(cli=t_rest(), port_ids=[port_id])
        assert_that(len(ports), equal_to(1))
        assert_that(ports[0].get_id(), equal_to(port_id))


class UnityIscsiPortalTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        portal = UnityIscsiPortal(cli=t_rest(), _id='if_4')
        assert_that(portal.ip_address, equal_to('10.244.213.177'))
        assert_that(portal.iscsi_node, instance_of(UnityIscsiNode))
        assert_that(portal.iscsi_node.name,
                    equal_to('iqn.1992-04.com.emc:cx.fnm00150600267.a0'))
        assert_that(portal.netmask, equal_to('255.255.255.0'))
        assert_that(portal.gateway, equal_to('10.244.213.1'))


class UnityIscsiPortalListTest(TestCase):
    @patch_rest
    def test_filter(self):
        port_id = 'spa_eth2'

        all_ports = UnityIscsiPortalList(cli=t_rest())
        ports = all_ports.shadow_copy(port_ids=[port_id])
        assert_that(len(ports), equal_to(2))
        assert_that(set(ports.id), equal_to(set(['if_4', 'if_5'])))

        ports = UnityIscsiPortalList(cli=t_rest(), port_ids=[port_id])
        assert_that(len(ports), equal_to(2))
        assert_that(set(ports.id), equal_to(set(['if_4', 'if_5'])))


class UnityFcPortTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        port = UnityFcPort('spa_fc4', cli=t_rest())
        assert_that(port.existed, equal_to(True))
        assert_that(port.slot_number, equal_to(4))
        assert_that(
            port.wwn,
            equal_to("50:06:01:60:C7:E0:01:DA:50:06:01:62:47:E0:01:DA"))
        assert_that(port.available_speeds,
                    only_contains(FcSpeedEnum._4GbPS,
                                  FcSpeedEnum._8GbPS,
                                  FcSpeedEnum._16GbPS,
                                  FcSpeedEnum.AUTO))
        assert_that(port.connector_type,
                    equal_to(ConnectorTypeEnum.LC))
        assert_that(port.name,
                    equal_to("SP A FC Port 4"))
        assert_that(port.storage_processor,
                    equal_to(UnityStorageProcessor('spa', cli=t_rest())))


class UnityFcPortListTest(TestCase):
    @patch_rest
    def test_filter(self):
        port_id = 'spa_iom_1_fc2'

        all_ports = UnityFcPortList(cli=t_rest())
        ports = all_ports.shadow_copy(port_ids=[port_id])
        assert_that(len(ports), equal_to(1))
        assert_that(ports[0].get_id(), equal_to(port_id))

        ports = UnityFcPortList(cli=t_rest(), port_ids=[port_id])
        assert_that(len(ports), equal_to(1))
        assert_that(ports[0].get_id(), equal_to(port_id))


class UnityIoLimitRuleTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        rule = UnityIoLimitRule('qr_1', cli=t_rest())
        assert_that(rule.get_id(), equal_to('qr_1'))
        assert_that(rule.max_iops, equal_to(1000))
        assert_that(rule.io_limit_policy.get_id(), equal_to('qp_1'))
        assert_that(rule.name, equal_to('Limit_1000_IOPS_rule'))


class UnityIoLimitPolicyTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        rule = UnityIoLimitPolicy('qp_2', cli=t_rest())
        assert_that(rule.description, contains_string('Absolute bandwidth'))
        assert_that(rule.existed, equal_to(True))
        assert_that(rule.get_id(), equal_to('qp_2'))
        assert_that(rule.is_shared, equal_to(False))
        lun_list = rule.luns
        assert_that(len(lun_list), equal_to(1))
        assert_that(rule.name, equal_to('Limit_2_MBPS'))
        assert_that(rule.state, equal_to(IOLimitPolicyStateEnum.ACTIVE))

        settings = rule.io_limit_rule_settings
        assert_that(len(settings), equal_to(1))

        setting = settings[0]
        assert_that(setting.burst_frequency, equal_to('01:00:00.000'))
        assert_that(setting.burst_time, equal_to('00:05:00.000'))
        assert_that(setting.get_id(), equal_to('qr_2'))
        assert_that(setting.max_kbps, equal_to(2048))
        assert_that(setting.name, equal_to('Limit_2_MBPS_rule'))

    @patch_rest
    def test_get_list(self):
        rule_list = UnityIoLimitPolicyList.get(cli=t_rest())
        assert_that(len(rule_list), equal_to(6))

    @patch_rest
    def test_create_kbps_policy(self):
        policy = UnityIoLimitPolicy.create(
            t_rest(), 'max_kbps_1234', max_kbps=1234, description='storops')
        assert_that(policy.name, equal_to('max_kbps_1234'))
        assert_that(policy.is_paused, equal_to(False))
        setting = policy.io_limit_rule_settings[0]
        assert_that(setting.max_kbps, equal_to(1234))
        assert_that(setting.name, equal_to('max_kbps_1234_rule'))

    @patch_rest
    def test_create_policy_existed(self):
        def f():
            UnityIoLimitPolicy.create(t_rest(), 'test1', max_kbps=1)

        assert_that(f, raises(UnityPolicyNameInUseError, 'been reserved'))

    @patch_rest
    def test_create_iops_policy(self):
        policy = UnityIoLimitPolicy.create(
            t_rest(), 'max_iops_4321', max_iops=4321, description='storops')
        assert_that(policy.name, equal_to('max_iops_4321'))
        assert_that(policy.is_paused, equal_to(False))
        setting = policy.io_limit_rule_settings[0]
        assert_that(setting.max_iops, equal_to(4321))
        assert_that(setting.name, equal_to('max_iops_4321_rule'))

    @patch_rest
    def test_delete_policy_not_found(self):
        def f():
            policy = UnityIoLimitPolicy('qp_8', t_rest())
            policy.delete()

        assert_that(f, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_apply_to_storage(self):
        policy = UnityIoLimitPolicy('qp_5', t_rest())
        lun1 = UnityLun('sv_2024', t_rest())
        lun2 = UnityLun('sv_2025', t_rest())
        resp = policy.apply_to_storage(lun1, lun2)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_remove_from_storage(self):
        policy = UnityIoLimitPolicy('qp_5', t_rest())
        lun1 = UnityLun('sv_2024', t_rest())
        lun2 = UnityLun('sv_2025', t_rest())
        resp = policy.remove_from_storage(lun1, lun2)
        assert_that(resp.is_ok(), equal_to(True))


class UnityLinkAggregationTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        la = UnityLinkAggregation('spa_la_2', cli=t_rest())
        assert_that(la.is_link_up, equal_to(False))
        assert_that(la.mac_address, equal_to('00:60:16:5C:08:E1'))
        assert_that(la.master_port.get_id(), "spa_eth2")
        assert_that(la.mtu, equal_to(9000))
        assert_that(
            la.parent_storage_processor,
            equal_to(UnityStorageProcessor.get(t_rest(), 'spa')))
        assert_that(len(la.ports), equal_to(2))
        assert_that(la.supported_mtus, only_contains(1500, 9000))

    @patch_rest
    def test_create(self):
        eth_2 = UnityEthernetPort.get(t_rest(), 'spa_eth2')
        eth_3 = UnityEthernetPort.get(t_rest(), 'spa_eth3')
        la = UnityLinkAggregation.create(t_rest(), [eth_2, eth_3], 9000)
        assert_that(la.get_id(), equal_to('spa_la_2'))

    @patch_rest
    def test_create_already_exist(self):
        def do():
            eth_2 = UnityEthernetPort.get(t_rest(), 'spa_eth2')
            eth_4 = UnityEthernetPort.get(t_rest(), 'spa_eth4')
            UnityLinkAggregation.create(t_rest(), [eth_2, eth_4], 1500)
        assert_that(do, raises(UnityEthernetPortAlreadyAggregatedError))

    @patch_rest
    def test_modify(self):
        la = UnityLinkAggregation.get(t_rest(), 'spa_la_2')
        la.modify(mtu=1500,
                  remove_ports=[UnityEthernetPort.get(t_rest(), "spa_eth2")],
                  add_ports=[UnityEthernetPort.get(t_rest(), "spa_eth4")])

    @patch_rest()
    def test_list_la_unsupported(self):
        def f():
            UnityLinkAggregation.get(t_rest("4.0.0"))
        assert_that(f, raises(SystemAPINotSupported))
