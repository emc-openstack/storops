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
from hamcrest import assert_that, equal_to, instance_of, only_contains, raises
from storops.exception import UnityEthernetPortSpeedNotSupportError, \
    UnityEthernetPortMtuSizeNotSupportError
from storops.unity.enums import ConnectorTypeEnum, EPSpeedValuesEnum
from storops.unity.resource.port import UnityEthernetPort, UnityIpPort, \
    UnityIpPortList, UnityIscsiPortal, UnityIscsiNode
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

    @ddt.data({'port_id': 'spa_eth2',
               'peer_id': 'spb_eth2'},
              {'port_id': 'spb_eth3',
               'peer_id': 'spa_eth3'})
    @ddt.unpack
    def test_get_peer(self, port_id, peer_id):
        port = UnityEthernetPort(cli=t_rest(), _id=port_id)
        peer = port.get_peer()
        assert_that(peer.get_id(), equal_to(peer_id))


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
