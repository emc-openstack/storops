# Copyright (c) 2018 Dell Inc. or its subsidiaries.
# All Rights Reserved.
#
#    Licensed under the Apache License, Veriion 2.0 (the "License"); you may
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
import unittest

import ddt
import hamcrest as hc

import storops
from storops.unity.resource import replication_interface, health, port, sp
from storops_test.unity import rest_mock as mock

__author__ = 'Ryan Liang'


@ddt.ddt
class UnityReplicationInterfaceTest(unittest.TestCase):
    @mock.patch_rest
    def test_get_properties(self):
        ri = replication_interface.UnityReplicationInterface.get(
            cli=mock.t_rest(), _id='if_10')
        hc.assert_that(ri.gateway, hc.equal_to('10.245.47.1'))
        hc.assert_that(ri.health, hc.instance_of(health.UnityHealth))
        hc.assert_that(ri.health.value, hc.equal_to(storops.HealthEnum.OK))
        hc.assert_that(ri.id, hc.equal_to('if_10'))
        hc.assert_that(ri.ip_address, hc.equal_to('10.245.47.99'))
        hc.assert_that(ri.ip_port, hc.instance_of(port.UnityIpPort))
        hc.assert_that(ri.ip_port.id, hc.equal_to('spa_eth2'))
        hc.assert_that(ri.ip_protocol_version,
                       hc.equal_to(storops.IpProtocolVersionEnum.IPv4))
        hc.assert_that(ri.mac_address, hc.equal_to('00:60:16:5C:07:0B'))
        hc.assert_that(ri.name, hc.equal_to('4_FNM00150600267'))
        hc.assert_that(ri.netmask, hc.equal_to('255.255.255.0'))
        hc.assert_that(ri.v6_prefix_length, hc.none())
        hc.assert_that(ri.vlan_id, hc.none())

    @mock.patch_rest
    def test_get_collection(self):
        ri_list = replication_interface.UnityReplicationInterfaceList.get(
            mock.t_rest())
        hc.assert_that(len(ri_list), hc.equal_to(2))
        hc.assert_that([ri.id for ri in ri_list],
                       hc.equal_to(['if_10', 'if_11']))

    @mock.patch_rest
    @ddt.data({'sp': sp.UnityStorageProcessor(_id='spa', cli=mock.t_rest()),
               'ip_port': port.UnityIpPort(_id='spa_eth3', cli=mock.t_rest()),
               'ip_address': '10.10.10.10', 'netmask': None,
               'v6_prefix_length': None, 'gateway': None, 'vlan_id': None},
              {'sp': sp.UnityStorageProcessor(_id='spa', cli=mock.t_rest()),
               'ip_port': port.UnityIpPort(_id='spa_eth3', cli=mock.t_rest()),
               'ip_address': '10.10.10.10', 'netmask': '255.255.255.0',
               'v6_prefix_length': None, 'gateway': '10.10.10.1',
               'vlan_id': 111})
    @ddt.unpack
    def test_create(self, sp, ip_port, ip_address, netmask, v6_prefix_length,
                    gateway, vlan_id):
        ri = replication_interface.UnityReplicationInterface.create(
            mock.t_rest(), sp, ip_port, ip_address, netmask=netmask,
            v6_prefix_length=v6_prefix_length, gateway=gateway,
            vlan_id=vlan_id)
        hc.assert_that(ri.id, hc.equal_to('if_10'))

    @mock.patch_rest
    @ddt.data({'sp': sp.UnityStorageProcessor(_id='spb', cli=mock.t_rest()),
               'ip_port': port.UnityIpPort(_id='spb_eth3', cli=mock.t_rest()),
               'ip_address': '10.10.20.10', 'netmask': '255.255.255.0',
               'v6_prefix_length': None, 'gateway': '10.10.20.1',
               'vlan_id': 222})
    @ddt.unpack
    def test_modify(self, sp, ip_port, ip_address, netmask, v6_prefix_length,
                    gateway, vlan_id):
        ri = replication_interface.UnityReplicationInterface.get(
            cli=mock.t_rest(), _id='if_10')
        resp = ri.modify(sp=sp, ip_port=ip_port, ip_address=ip_address,
                         netmask=netmask, v6_prefix_length=v6_prefix_length,
                         gateway=gateway, vlan_id=vlan_id)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))
