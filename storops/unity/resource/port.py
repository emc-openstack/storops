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

import logging

from storops.unity.resource import UnityResource, UnityResourceList
from storops.exception import UnityEthernetPortMtuSizeNotSupportError
from storops.exception import UnityEthernetPortSpeedNotSupportError
from storops.unity.enums import EPSpeedValuesEnum

__author__ = 'Jay Xu'

LOG = logging.getLogger(__name__)


class UnityIpPort(UnityResource):
    pass


class UnityIpPortList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityIpPort


class UnityFcPort(UnityResource):
    pass


class UnityFcPortList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityFcPort


class UnityIoModule(UnityResource):
    pass


class UnityIoModuleList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityIoModule


class UnityIoLimitPolicy(UnityResource):
    pass


class UnityIoLimitPolicyList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityIoLimitPolicy


class UnityIoLimitRule(UnityResource):
    pass


class UnityIoLimitRuleList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityIoLimitRule


class UnityIscsiPortal(UnityResource):
    @classmethod
    def get_nested_properties(cls):
        return 'iscsi_node.name'


class UnityIscsiPortalList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityIscsiPortal


class UnityEthernetPort(UnityResource):
    def modify(self, speed=None, mtu=None):
        speed = EPSpeedValuesEnum.parse(speed)
        peer = self.get_peer()
        self._modify(self, speed, mtu)
        self._modify(peer, speed, mtu)

    def get_peer(self):
        _peer_id = self._get_peer_id(self.get_id())
        return UnityEthernetPort(cli=self._cli, _id=_peer_id)

    def _modify(self, port, speed, mtu):
        if speed is not None:
            if speed not in self.supported_speeds:
                raise UnityEthernetPortSpeedNotSupportError
            if speed == port.requested_speed:
                speed = None

        if mtu is not None:
            if mtu not in self.supported_mtus:
                raise UnityEthernetPortMtuSizeNotSupportError
            if mtu == port.requested_mtu:
                mtu = None

        if speed is None and mtu is None:
            return

        resp = self._cli.modify(self.resource_class,
                                port.get_id(),
                                speed=speed, mtuSize=mtu)
        resp.raise_if_err()

    @staticmethod
    def _get_peer_id(_id):
        if _id.startswith('spa'):
            return _id.replace('spa', 'spb')
        return _id.replace('spb', 'spa')


class UnityEthernetPortList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityEthernetPort


class UnityIscsiNode(UnityResource):
    pass


class UnityIscsiNodeList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityIscsiNode
