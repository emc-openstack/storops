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

from storops.lib.common import instance_cache
from storops.unity.resource import UnityResource, UnityResourceList, \
    UnityAttributeResource
from storops.exception import UnityEthernetPortMtuSizeNotSupportError
from storops.exception import UnityEthernetPortSpeedNotSupportError
from storops.unity.enums import EPSpeedValuesEnum, IOLimitPolicyTypeEnum
from storops.lib.version import version

__author__ = 'Jay Xu'

LOG = logging.getLogger(__name__)


class UnityIpPort(UnityResource):
    def set_mtu(self, mtu):
        port = self.get_physical_port()
        port.modify(mtu=mtu)

    @instance_cache
    @version('>=4.1')
    def is_link_aggregation(self):
        port = UnityLinkAggregation.get(self._cli, self.get_id())
        return port.existed

    @instance_cache  # noqa
    @version('<4.1')
    def is_link_aggregation(self):
        # Link aggregation is not supported before Falcon 4.1
        return False

    def get_physical_port(self):
        """Returns the link aggregation object or the ethernet port object."""
        obj = None
        if self.is_link_aggregation():
            obj = UnityLinkAggregation.get(self._cli, self.get_id())
        else:
            obj = UnityEthernetPort.get(self._cli, self.get_id())
        return obj

    @property
    def mtu(self):
        port = self.get_physical_port()
        return port.mtu


class UnityIpPortList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityIpPort


class UnityFcPort(UnityResource):
    pass


class UnityFcPortList(UnityResourceList):
    def __init__(self, cli=None, port_ids=None, **filters):
        super(UnityFcPortList, self).__init__(cli, **filters)
        self._port_ids = None
        self._set_filter(port_ids)

    def _set_filter(self, port_ids=None, **kwargs):
        self._port_ids = port_ids

    def _filter(self, fc_port):
        ret = True
        if self._port_ids is not None:
            ret &= fc_port.get_id() in self._port_ids
        return ret

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
    @classmethod
    def create(cls, cli, name, max_iops=None, max_kbps=None,
               policy_type=None, is_shared=None, description=None):
        if policy_type is None:
            policy_type = IOLimitPolicyTypeEnum.ABSOLUTE
        if is_shared is None:
            is_shared = False

        rule = cli.make_body(name='{}_rule'.format(name),
                             maxIOPS=max_iops,
                             maxKBPS=max_kbps)
        resp = cli.post(cls().resource_class,
                        name=name,
                        description=description,
                        isShared=is_shared,
                        type=policy_type,
                        ioLimitRules=[rule])
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def apply_to_storage(self, *lun_list):
        return self._cli.action(self.resource_class, self.get_id(),
                                'applyToStorage', luns=lun_list)

    def remove_from_storage(self, *lun_list):
        return self._cli.action(self.resource_class, self.get_id(),
                                'removeFromStorage', luns=lun_list)


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


class UnityIoLimitRuleSetting(UnityAttributeResource):
    pass


class UnityIoLimitRuleSettingList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityIoLimitRuleSetting


class UnityIscsiPortal(UnityResource):
    @classmethod
    def get_nested_properties(cls):
        return 'iscsi_node.name'


class UnityIscsiPortalList(UnityResourceList):
    def __init__(self, cli=None, port_ids=None, **filters):
        super(UnityIscsiPortalList, self).__init__(cli, **filters)
        self._port_ids = None
        self._set_filter(port_ids)

    def _set_filter(self, port_ids=None, **kwargs):
        self._port_ids = port_ids

    def _filter(self, iscsi_portal):
        ret = True
        if self._port_ids is not None:
            ret &= iscsi_portal.ethernet_port.get_id() in self._port_ids
        return ret

    @classmethod
    def get_resource_class(cls):
        return UnityIscsiPortal


class UnityEthernetPort(UnityResource):
    def modify(self, speed=None, mtu=None):
        speed = EPSpeedValuesEnum.parse(speed)
        self._modify(self, speed, mtu)
        peer = self.get_peer()
        if peer.existed:
            self._modify(peer, speed, mtu)

    def get_peer(self):
        peer_id = self._get_peer_id(self.get_id())
        return UnityEthernetPort(cli=self._cli, _id=peer_id)

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
    def __init__(self, cli=None, port_ids=None, **filters):
        super(UnityEthernetPortList, self).__init__(cli, **filters)
        self._port_ids = None
        self._set_filter(port_ids)

    def _set_filter(self, port_ids=None, **kwargs):
        self._port_ids = port_ids

    def _filter(self, ethernet_port):
        ret = True
        if self._port_ids is not None:
            ret &= ethernet_port.get_id() in self._port_ids
        return ret

    @classmethod
    def get_resource_class(cls):
        return UnityEthernetPort


@version(">=4.1")
class UnityLinkAggregation(UnityResource):
    @classmethod
    def create(cls, cli, ports, mtu=None):
        resp = cli.post(cls().resource_class,
                        ports=ports,
                        mtuSize=mtu)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def modify(self, mtu=None, add_ports=None, remove_ports=None):
        if isinstance(add_ports, UnityEthernetPort):
            add_ports = [add_ports]
        if isinstance(remove_ports, UnityEthernetPort):
            remove_ports = [remove_ports]

        resp = self._cli.modify(self.resource_class,
                                self.get_id(),
                                mtuSize=mtu,
                                addPorts=add_ports,
                                removePorts=remove_ports)
        resp.raise_if_err()


@version(">=4.1")
class UnityLinkAggregationList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityLinkAggregation


class UnityIscsiNode(UnityResource):
    pass


class UnityIscsiNodeList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityIscsiNode
