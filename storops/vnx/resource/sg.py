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

import logging
import random
from threading import Lock

from retryz import retry

import storops.vnx.resource.host
import storops.vnx.resource.lun
from storops import exception as ex
from storops.lib.common import instance_cache
from storops.vnx.enums import VNXPortType
from storops.vnx.resource import VNXCliResource, VNXCliResourceList
from storops.vnx.resource.port import VNXHbaPort

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class VNXStorageGroup(VNXCliResource):
    def __init__(self, name=None, cli=None, shuffle_hlu=True,
                 system_lun_list=None):
        super(VNXStorageGroup, self).__init__()
        self._cli = cli
        self._name = name
        self._system_lun_list = system_lun_list

        self._uid = ''
        self._hba_port_list = []
        self._conn = None
        self._hlu_lock = Lock()

        self.shuffle_hlu = shuffle_hlu

    def _get_raw_resource(self):
        return self._cli.get_sg(name=self._name, poll=self.poll,
                                engineering=True)

    @classmethod
    def get(cls, cli, name=None, system_lun_list=None):
        if name is None:
            ret = VNXStorageGroupList(cli, system_lun_list=system_lun_list)
        else:
            ret = VNXStorageGroup(name, cli, system_lun_list=system_lun_list)
        return ret

    @classmethod
    def create(cls, name, cli):
        out = cli.create_sg(name)
        msg = 'failed to create storage group "{}".'.format(name)
        ex.raise_if_err(out, msg, default=ex.VNXCreateStorageGroupError)
        return VNXStorageGroup(name, cli)

    def delete(self, disconnect_host=False):
        if disconnect_host:
            for hba in self.hba_sp_pairs:
                self.disconnect_host(hba.host_name)
        out = self._cli.delete_sg(self._get_name(), poll=self.poll)
        ex.raise_if_err(out, default=ex.VNXDeleteStorageGroupError)

    def has_hlu(self, hlu):
        return hlu in self.used_hlu_numbers

    def has_alu(self, lun):
        try:
            alu = storops.vnx.resource.lun.VNXLun.get_id(lun)
        except ValueError:
            # lun not found, id is None
            alu = None
        return alu is not None and alu in self.used_alu_numbers

    def get_hlu(self, lun):
        alu = storops.vnx.resource.lun.VNXLun.get_id(lun)
        return self.get_alu_hlu_map().get(alu, None)

    def is_valid(self):
        return len(self.name) > 0 and len(self.uid) > 0

    @property
    def hosts(self):
        host_names = [pair.host_name for pair in self.hba_sp_pairs]
        clz = storops.vnx.resource.host.VNXHostList
        return clz(cli=self._cli, names=host_names)

    @property
    @instance_cache
    def lun_list(self):
        lun_ids = self.get_alu_hlu_map().keys()
        if self._system_lun_list is not None:
            ret = self._system_lun_list.shadow_copy(lun_ids=lun_ids)
        else:
            clz = storops.vnx.resource.lun.VNXLunList
            ret = clz(cli=self._cli, lun_ids=lun_ids)
        ret.poll = self.poll
        return ret

    @property
    def hba_port_list(self):
        if not self._hba_port_list:
            self.hba_port_list = self.hba_sp_pairs
        return self._hba_port_list

    @hba_port_list.setter
    def hba_port_list(self, hba_sp_pairs):
        def _process_cli_output(value):
            port = VNXHbaPort.from_storage_group_hba(value)
            hba = value.uid
            self._hba_port_list.append((hba, port))

        if hba_sp_pairs is not None:
            for item in hba_sp_pairs:
                _process_cli_output(item)

    @staticmethod
    def _port_filter(ports, sp=None, port_id=None, vport_id=None,
                     port_type=None):
        def _filter(port):
            ret = True
            if sp is not None:
                ret &= port.sp == sp
            if port_id is not None:
                ret &= port.port_id == port_id
            if vport_id is not None:
                ret &= port.vport_id == vport_id
            if port_type is not None:
                ret &= port.type == port_type
            return ret

        return tuple(filter(_filter, ports))

    def _get_hba_ports(self, sp=None, port_id=None, vport_id=None,
                       port_type=None):
        ports = set(map(lambda x: x[1], self.hba_port_list))
        return self._port_filter(ports, sp, port_id, vport_id, port_type)

    def get_ports(self, initiator_uid=None, sp=None, port_id=None,
                  vport_id=None, port_type=None):
        if initiator_uid is not None:
            ret = []
            for hba, port in self.hba_port_list:
                if hba == initiator_uid:
                    ret.append(port)
            ret = tuple(set(ret))
        else:
            ret = self._get_hba_ports(sp, port_id, vport_id, port_type)
        return ret

    def get_fc_ports(self, initiator_uid=None, sp=None, port_id=None,
                     vport_id=None):
        return self.get_ports(initiator_uid=initiator_uid,
                              sp=sp,
                              port_id=port_id,
                              vport_id=vport_id,
                              port_type=VNXPortType.FC)

    def get_iscsi_ports(self, initiator_uid=None, sp=None, port_id=None,
                        vport_id=None):
        return self.get_ports(initiator_uid=initiator_uid,
                              sp=sp,
                              port_id=port_id,
                              vport_id=vport_id,
                              port_type=VNXPortType.ISCSI)

    @property
    def ports(self):
        return self.get_ports()

    @property
    def iscsi_ports(self):
        return self.get_ports(port_type=VNXPortType.ISCSI)

    @property
    def fc_ports(self):
        return self.get_ports(port_type=VNXPortType.FC)

    @property
    def initiator_uid_list(self):
        if self.hba_sp_pairs is not None:
            ret = tuple(set(map(lambda x: x.uid, self.hba_sp_pairs)))
        else:
            ret = tuple()
        return ret

    def get_initiator_uids(self, port_type=None):
        ret = []
        for hba, port in self.hba_port_list:
            if port_type is not None:
                if port.type == port_type:
                    ret.append(hba)
            else:
                ret.append(hba)
        return tuple(set(ret))

    _hlu_full = None
    _max_hlu = 255

    @classmethod
    def get_max_luns_per_sg(cls):
        return cls._max_hlu

    @classmethod
    def set_max_luns_per_sg(cls, value):
        log.info('Update max LUNs per storage group to: {}'
                 .format(value))
        cls._max_hlu = value
        cls._hlu_full = None

    @classmethod
    def _hlu_full_set(cls):
        if cls._hlu_full is None:
            cls._hlu_full = set(range(1, cls.get_max_luns_per_sg() + 1))
        return set(cls._hlu_full)

    def get_alu_hlu_map(self):
        if self.alu_hlu_map is None:
            self._parsed_resource['alu_hlu_map'] = {}
        return self.alu_hlu_map

    @property
    def used_hlu_numbers(self):
        return self.get_alu_hlu_map().values()

    @property
    def used_alu_numbers(self):
        return self.get_alu_hlu_map().keys()

    def _get_hlu_to_add(self, alu):
        ret = None
        with self._hlu_lock:
            remain = self._hlu_full_set() - set(self.used_hlu_numbers)
            if len(remain) == 0:
                raise ex.VNXNoHluAvailableError(
                    'no hlu number available for attach.')
            if self.shuffle_hlu:
                ret = random.sample(remain, 1)[0]
            else:
                ret = remain.pop()
            self.get_alu_hlu_map()[alu] = ret
        return ret

    def _add_hlu(self, alu, hlu):
        with self._hlu_lock:
            self.get_alu_hlu_map()[alu] = hlu
        return hlu

    def _delete_alu(self, alu):
        ret = None
        with self._hlu_lock:
            if self.has_alu(alu):
                ret = self.get_alu_hlu_map().pop(alu)
        return ret

    def attach_alu(self, lun, retry_limit=None, hlu=None):
        def _update():
            self.update()

        @retry(on_error=ex.VNXHluNumberInUseError, on_retry=_update,
               limit=retry_limit)
        def _do(alu_id, hlu_id=None):
            if hlu_id is None:
                hlu_id = self._get_hlu_to_add(alu_id)
            elif hlu_id in self.used_hlu_numbers:
                raise ex.VNXHluAlreadyUsedError('hlu id is already used.')
            else:
                hlu_id = self._add_hlu(alu_id, hlu_id)
            out = self._cli.sg_add_hlu(self._get_name(), hlu_id, alu_id,
                                       poll=self.poll)
            try:
                ex.raise_if_err(out, default=ex.VNXAttachAluError)
            except ex.VNXAluAlreadyAttachedError:
                # alu no in the alu-hlu map cache but attach failed with
                # already attached, that means the cache is out dated
                self.update()
                raise
            except ex.VNXAttachAluError:
                # other attach error, remove hlu id from the cache
                self._delete_alu(alu_id)
                raise

            return hlu_id

        lun_clz = storops.vnx.resource.lun.VNXLun
        alu = lun_clz.get_id(lun)
        if self.has_alu(alu):
            # found alu in the alu-hlu map cache, meaning already attached
            raise ex.VNXAluAlreadyAttachedError()
        else:
            ret = _do(alu, hlu)
        return ret

    def detach_alu(self, lun):
        alu = storops.vnx.resource.lun.VNXLun.get_id(lun)
        hlu = self.get_hlu(lun)
        if hlu is None:
            raise ex.VNXDetachAluNotFoundError(
                'specified lun {} is not attached.'.format(alu))
        out = self._cli.sg_delete_hlu(self._get_name(), hlu, poll=self.poll)
        msg = 'failed to detach hlu {}/alu {}.'.format(hlu, alu)
        ex.raise_if_err(out, msg, default=ex.VNXStorageGroupError, )
        self._delete_alu(alu)

    def connect_host(self, host):
        out = self._cli.sg_connect_host(self._get_name(), host, poll=self.poll)
        msg = 'failed to connect host {}.'.format(host)
        ex.raise_if_err(out, msg, default=ex.VNXStorageGroupError)

    def disconnect_host(self, host):
        out = self._cli.sg_disconnect_host(self._get_name(), host,
                                           poll=self.poll)
        msg = 'failed to disconnect host {}.'.format(host)
        ex.raise_if_err(out, msg, default=ex.VNXStorageGroupError)

    def connect_hba(self, port, hba_uid, host_name, host_ip=None):
        return self.set_path(port, hba_uid, host_name, host_ip)

    @property
    def uid(self):
        return self.wwn

    def set_path(self, port, hba_uid, host_name, host_ip=None):
        if hasattr(port, 'sp'):
            sp = port.sp
        else:
            raise ValueError('sp is not available from {}.'.format(port))

        if hasattr(port, 'port_id'):
            port_id = port.port_id
        else:
            raise ValueError('port id is not available from {}.'.format(port))

        vport_id = None
        if hasattr(port, 'virtual_port_id'):
            # FCoE do not need vport_id
            if hasattr(port, 'type'):
                port_type = port.type
                if port_type == VNXPortType.ISCSI:
                    vport_id = port.virtual_port_id

        out = self._cli.set_path(self._get_name(), hba_uid, sp, port_id,
                                 host_ip, host_name, vport_id=vport_id)
        ex.raise_if_err(out)

    def set_system_lun_list(self, system_lun_list):
        self._system_lun_list = system_lun_list


class VNXStorageGroupList(VNXCliResourceList):
    @classmethod
    def get_resource_class(cls):
        return VNXStorageGroup

    def __init__(self, cli=None, engineering=False, system_lun_list=None):
        super(VNXStorageGroupList, self).__init__(cli)
        self._sg_map = {}
        self._engineering = engineering
        self._system_lun_list = system_lun_list

    def add_sg(self, sg):
        self._sg_map[sg.name] = sg

    def detach_alu(self, lun):
        for sg in self:
            if sg.has_alu(lun):
                sg.detach_alu(lun)

    def _get_raw_resource(self):
        return self._cli.get_sg(poll=self.poll, engineering=self._engineering)

    @property
    @instance_cache
    def _name_sg_map(self):
        return {sg.name: sg for sg in self}

    def _get_resource_instance(self):
        ret = super(VNXStorageGroupList, self)._get_resource_instance()
        ret.set_system_lun_list(self._system_lun_list)
        return ret

    def get(self, name):
        if isinstance(name, VNXStorageGroup):
            name = name.name

        return self._name_sg_map.get(name)
