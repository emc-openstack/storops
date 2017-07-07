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
from storops.lib.converter import from_hour, from_minute
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
               policy_type=None, is_shared=None, description=None,
               max_iops_density=None, max_kbps_density=None,
               burst_rate=None, burst_time=None, burst_frequency=None):
        if policy_type is None:
            policy_type = IOLimitPolicyTypeEnum.ABSOLUTE
        if is_shared is None:
            is_shared = False

        rule = cli.make_body(name='{}_rule'.format(name),
                             maxIOPS=max_iops,
                             maxKBPS=max_kbps,
                             maxIOPSDensity=max_iops_density,
                             maxKBPSDensity=max_kbps_density,
                             burstRate=burst_rate,
                             burstTime=from_minute(burst_time),
                             burstFrequency=from_hour(burst_frequency))
        resp = cli.post(cls().resource_class,
                        name=name,
                        description=description,
                        isShared=is_shared,
                        type=policy_type,
                        ioLimitRules=[rule])
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def modify(self, name=None, policy_type=None,
               is_paused=None, max_iops=None, max_kbps=None,
               max_iops_density=None, max_kbps_density=None,
               description=None, is_shared=None,
               burst_rate=None, burst_time=None, burst_frequency=None):
        # name = self.name if name is None else self.name
        rule = self._cli.make_body(maxIOPS=max_iops,
                                   maxKBPS=max_kbps,
                                   maxIOPSDensity=max_iops_density,
                                   maxKBPSDensity=max_kbps_density,
                                   burstRate=burst_rate,
                                   burstTime=from_minute(burst_time),
                                   burstFrequency=from_hour(burst_frequency),
                                   id=self.io_limit_rule_settings[0].get_id())
        resp = self._cli.modify(self.resource_class, self.get_id(),
                                name=name,
                                description=description,
                                isShared=is_shared,
                                type=policy_type,
                                ioLimitRulesToModify=[rule])
        resp.raise_if_err()
        return self

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

    @classmethod
    def create(cls, cli, ethernet_port, ip, netmask=None,
               v6_prefix_len=None, vlan=None, gateway=None):
        if not isinstance(ethernet_port, UnityEthernetPort):
            ethernet_port = UnityEthernetPort.get(cli, _id=ethernet_port)

        req_body = cli.make_body(
            ethernetPort=ethernet_port,
            ipAddress=ip,
            netmask=netmask,
            v6PrefixLength=v6_prefix_len,
            vlanId=vlan,
            gateway=gateway,
        )
        resp = cli.post(cls().resource_class, **req_body)
        resp.raise_if_err()
        return cls(cli=cli, _id=resp.resource_id)

    def modify(self, ip=None, netmask=None,
               v6_prefix_len=None, vlan=None, gateway=None):
        req_body = self._cli.make_body(
            ipAddress=ip,
            netmask=netmask,
            v6PrefixLength=v6_prefix_len,
            vlanId=vlan,
            gateway=gateway
        )
        resp = self._cli.modify(self.resource_class,
                                self.get_id(), **req_body)
        resp.raise_if_err()
        return resp


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

    @property
    def parent_storage_processor(self):
        # For ports on IO modules, there is no `parent_storage_processor`.
        # Set it manually.
        return self.storage_processor


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
    @classmethod
    def get_nested_properties(cls):
        return (
            'ethernet_port.connector_type',
            'ethernet_port.speed',
            'ethernet_port.supported_speeds',
            'ethernet_port.health',
        )


class UnityIscsiNodeList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityIscsiNode


class UnitySasPort(UnityResource):
    @classmethod
    def get_nested_properties(cls):
        return (
            'parentIOModule.name',
            'parent_storage_processor.name',
        )


class UnitySasPortList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySasPort
