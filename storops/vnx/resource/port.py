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

from storops.exception import raise_if_err, VNXPingNodeError, \
    VNXPingNodeSuccess, VNXPortError
from storops.lib.common import check_int, instance_cache
from storops.vnx.enums import VNXSPEnum, VNXPortType
from storops.vnx.resource import VNXCliResourceList, VNXCliResource

__author__ = 'Cedric Zhuang'


class VNXPort(VNXCliResource):
    """ Base class for all kinds of ports

    Include the basic property like sp, port_id and vport_id.
    """

    @property
    def sp(self):
        return VNXSPEnum.parse(self._get_property('_sp'))

    @property
    def port_id(self):
        return self._get_property('_port_id')

    @property
    def vport_id(self):
        return self._get_property('_vport_id')

    @property
    def wwn(self):
        return self._get_property('_wwn')

    @property
    @instance_cache
    def index(self):
        sp = 'A' if self.sp == VNXSPEnum.SP_A else 'B'
        if self.vport_id is not None:
            ret = '{}_{}_{}'.format(sp, self.port_id, self.vport_id)
        else:
            ret = '{}_{}'.format(sp, self.port_id)
        return ret

    @property
    def display_name(self):
        items = [self.sp.display_name, str(self.port_id)]
        if self.vport_id is not None:
            items.append(str(self.vport_id))
        return '-'.join(items)

    def config_ip(self, ip, mask, gateway, vport_id=None, vlan_id=None):
        if self.type != VNXPortType.ISCSI:
            raise TypeError('configure IP only works for iSCSI ports.')
        if vport_id is None:
            vport_id = self.vport_id

        out = self._cli.config_iscsi_ip(
            self.sp, self.port_id, ip, mask, gateway, vport_id=vport_id,
            vlan_id=vlan_id)
        raise_if_err(out, default=VNXPortError)

        if vport_id is None:
            vport_id = 0
        return VNXConnectionPort(self.sp, self.port_id, vport_id, self._cli)

    def delete_ip(self, vport_id=None):
        if self.type != VNXPortType.ISCSI:
            raise TypeError('delete IP only works for iSCSI ports.')
        if vport_id is None:
            vport_id = self.vport_id

        out = self._cli.delete_iscsi_ip(self.sp, self.port_id, vport_id)
        raise_if_err(out, default=VNXPortError)

    @classmethod
    def delete_hba(cls, cli, hba_uid):
        out = cli.delete_hba(hba_uid)
        raise_if_err(out)

    def _get_property(self, prop_name):
        ret = None
        if hasattr(self, prop_name):
            ret = getattr(self, prop_name)

        if ret is None:
            try:
                striped_name = prop_name.strip('_')
                ret = self._get_property_from_raw(striped_name)
            except AttributeError:
                pass
        return ret

    def __hash__(self):
        return hash('<VNXPort {{sp: {}, port_id: {}, vport_id: {}}}'
                    .format(self.sp, self.port_id, self.vport_id))

    @staticmethod
    def _get_inst_prop(instance, name):
        if hasattr(instance, name):
            ret = getattr(instance, name)
        else:
            ret = None
        return ret

    def __eq__(self, other):
        o_sp = self._get_inst_prop(other, 'sp')
        o_port_id = self._get_inst_prop(other, 'port_id')
        o_vport_id = self._get_inst_prop(other, 'vport_id')

        ret = True
        ret &= self.sp == o_sp
        ret &= self.port_id == o_port_id
        ret &= self.vport_id == o_vport_id

        return ret


class VNXSPPortList(VNXCliResourceList):
    def __init__(self, cli, sp=None, port_id=None, port_type=None):
        super(VNXSPPortList, self).__init__(cli=cli)
        self._sp = sp
        self._port_id = port_id
        self._port_type = port_type

    def _filter(self, item):
        ret = True

        if self._sp is not None:
            ret &= item.sp == self._sp

        if self._port_id is not None:
            ret &= item.port_id == self._port_id

        if self._port_type is not None:
            ret &= item.type == self._port_type

        return ret

    @classmethod
    def get_resource_class(cls):
        return VNXSPPort

    def _get_raw_resource(self):
        return self._cli.get_sp_port(poll=self.poll)

    @property
    @instance_cache
    def _port_index_map(self):
        return {port.index: port for port in self}

    def get(self, index):
        if isinstance(index, VNXSPPort):
            index = index.index

        return self._port_index_map.get(index)


class VNXSPPort(VNXPort):
    def __init__(self, sp=None, port_id=None, cli=None):
        super(VNXSPPort, self).__init__()
        self._cli = cli
        self._sp = sp
        self._port_id = port_id

    def _get_raw_resource(self):
        raise ValueError('Cannot get single sp port info from cli.  '
                         'Use {}.get(sp, port_id, cli) instead.'
                         .format(self.__class__.__name__))

    @classmethod
    def get(cls, cli, sp=None, port_id=None, port_type=None):
        return VNXSPPortList(cli, sp=sp, port_id=port_id, port_type=port_type)

    @property
    def type(self):
        return VNXPortType.parse(self.wwn)

    def property_names(self):
        ret = super(VNXSPPort, self).property_names()
        ret.append('type')
        return ret


class VNXHbaPort(VNXPort):
    @classmethod
    def _get_parser(cls):
        raise ValueError('property not found.')

    def __init__(self, sp, port_id, vport_id=None):
        super(VNXHbaPort, self).__init__()
        self._sp = VNXSPEnum.parse(sp)
        self._port_id = check_int(port_id)
        self._vport_id = check_int(vport_id, allow_none=True)
        self._type = VNXPortType.FC
        self._host_initiator_list = []

    def is_valid(self):
        return self.sp is not None and self.port_id is not None

    @property
    def sp(self):
        return self._sp

    def get_sp_index(self):
        return VNXSPEnum.get_sp_index(self.sp)

    @property
    def port_id(self):
        return self._port_id

    @property
    def vport_id(self):
        return self._vport_id

    @property
    def type(self):
        ret = None
        if self.host_initiator_list:
            ret = VNXPortType.parse(self.host_initiator_list[0])
        return ret

    @property
    def host_initiator_list(self):
        return tuple(self._host_initiator_list)

    @staticmethod
    def create(sp, port_id, port_type=VNXPortType.FC, vport_id=None):
        port = VNXHbaPort(sp, port_id, vport_id)
        port._type = port_type
        return port

    @staticmethod
    def from_storage_group_hba(sg_hba):
        port = VNXHbaPort.create(sg_hba.sp, sg_hba.port_id,
                                 vport_id=sg_hba.vlan)
        port._host_initiator_list.append(sg_hba.hba[0])
        return port

    def as_tuple(self):
        return self.sp, self.port_id

    def get_index(self):
        return 'sp'

    def property_names(self):
        return ['sp', 'port_id', 'vport_id', 'type',
                'host_initiator_list']


class VNXConnectionPortList(VNXCliResourceList):
    def __init__(self, cli, sp=None, port_id=None, vport_id=None,
                 port_type=None, has_ip=None):
        super(VNXConnectionPortList, self).__init__(cli=cli)
        self._sp = sp
        self._port_id = port_id
        self._vport_id = vport_id
        self._port_type = port_type
        self._has_ip = has_ip

    def _filter(self, item):
        ret = True
        if self._sp is not None:
            ret &= item.sp == self._sp

        if self._port_id is not None:
            ret &= item.port_id == self._port_id

        if self._vport_id is not None:
            ret &= item.virtual_port_id == self._vport_id

        if self._port_type is not None:
            ret &= item.type == self._port_type

        if self._has_ip is not None:
            if self._has_ip:
                ret &= item.ip_address is not None
            else:
                ret &= item.ip_address is None
        return ret

    @classmethod
    def get_resource_class(cls):
        return VNXConnectionPort

    def _get_raw_resource(self):
        return self._cli.get_connection_port(poll=self.poll)


class VNXConnectionPort(VNXPort):
    def __init__(self, sp=None, port_id=None, vport_id=None, cli=None):
        super(VNXConnectionPort, self).__init__()
        self._sp = sp
        self._port_id = port_id
        self._vport_id = vport_id
        self._cli = cli

    @property
    def vport_id(self):
        if self._vport_id is not None:
            ret = self._vport_id
        else:
            ret = self.virtual_port_id
        return ret

    @property
    def type(self):
        ret = VNXPortType.parse(self.wwn)
        if ret == VNXPortType.FC and self.virtual_port_id is not None:
            ret = VNXPortType.FCOE
        return ret

    @property
    def existed(self):
        return self.wwn is not None

    def _get_raw_resource(self):
        return self._cli.get_connection_port(
            sp=self._sp, port_id=self._port_id, vport_id=self._vport_id,
            poll=self.poll)

    def property_names(self):
        names = super(VNXConnectionPort, self).property_names()
        names.append('type')
        return names

    @classmethod
    def get(cls, cli, sp=None, port_id=None, vport_id=None, port_type=None,
            has_ip=None):
        VNXPortType.verify(port_type)
        if sp is not None and port_id is not None and vport_id is not None:
            ret = VNXConnectionPort(sp, port_id, vport_id, cli)
            if port_type is not None and ret.type != port_type:
                ret = None
        else:
            ret = VNXConnectionPortList(cli, sp, port_id, vport_id, port_type,
                                        has_ip)
        return ret

    def ping_node(self, address, packet_size=None, count=None, timeout=None,
                  delay=None):
        out = self._cli.ping_node(address=address,
                                  sp=self.sp,
                                  port_id=self.port_id,
                                  vport_id=self.virtual_port_id,
                                  packet_size=packet_size,
                                  count=count,
                                  timeout=timeout,
                                  delay=delay)
        try:
            raise_if_err(out, default=VNXPingNodeError)
        except VNXPingNodeSuccess:
            # ping success, pass
            pass


class VNXStorageGroupHBA(VNXPort):
    @property
    def sp(self):
        return VNXSPEnum.parse(self.hba[1])

    @property
    def port_id(self):
        return int(self.hba[2])

    @property
    def uid(self):
        return self.hba[0]

    @property
    def vlan(self):
        sp_port = self.sp_port
        ret = None

        if self.type == VNXPortType.ISCSI:
            # vport only valid for iSCSI
            if sp_port is not None and 'v' in sp_port:
                ret = int(sp_port[sp_port.find('v') + 1:])
        return ret

    @property
    def vport_id(self):
        return self.vlan

    @property
    def port_type(self):
        return self.type

    @property
    def type(self):
        ret = None
        if '.' in self.uid:
            ret = VNXPortType.ISCSI
        elif ':' in self.uid:
            ret = VNXPortType.FC
        return ret

    def property_names(self):
        ret = super(VNXStorageGroupHBA, self).property_names()
        return ret + ['uid', 'sp', 'port_id', 'vport_id', 'vlan', 'port_type']


class VNXStorageGroupHBAList(VNXCliResourceList):
    @classmethod
    def get_resource_class(cls):
        return VNXStorageGroupHBA
