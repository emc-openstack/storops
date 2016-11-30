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
import re
from datetime import datetime

from past.builtins import filter

from storops.lib.common import clear_instance_cache
from storops.lib.converter import to_datetime
from storops.vnx.enums import VNXSPEnum
from storops.vnx.resource import VNXCliResourceList, VNXCliResource, \
    WithListPoll

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class VNXStorageProcessor(VNXCliResource):
    def __init__(self, cli, sp=None, ip=None):
        super(VNXStorageProcessor, self).__init__()
        self._cli = cli
        self._sp = sp
        self._ip = ip

    @property
    def enum(self):
        return self._sp

    @property
    def system_timestamp(self):
        return to_datetime('{} {}'.format(self.system_date, self.system_time))

    def _get_raw_resource(self):
        sps = self._cli.get_sp(poll=self.poll).split('SP B')
        out = ''
        if sps:
            if self._sp is VNXSPEnum.SP_A:
                out = sps[0]
            elif len(sps) > 1:
                out = sps[1]

        control_out = self._cli.get_control(ip=self._ip, poll=self.poll)
        return 'SP {}\n{}\n{}'.format(self._sp.index.upper(), control_out, out)


class VNXStorageProcessorList(VNXCliResourceList):
    def __init__(self, *sp_list):
        if len(sp_list) > 0:
            cli = sp_list[0]._cli
        else:
            raise ValueError('expect at least one sp.')
        super(VNXStorageProcessorList, self).__init__(cli=cli)
        self._list = sp_list
        self._cli = cli

    def with_poll(self):
        ret = WithListPoll(self)
        for rsc in self:
            rsc.poll = True
        return ret

    def with_no_poll(self):
        ret = WithListPoll(self)
        for rsc in self:
            rsc.poll = False
        return ret

    @classmethod
    def get_resource_class(cls):
        return VNXStorageProcessor

    @clear_instance_cache
    def update(self, data=None):
        for sp in self:
            sp.update()
        self.timestamp = datetime.now()

    def get(self, sp):
        if isinstance(sp, VNXStorageProcessor):
            sp = sp.enum

        for s in self:
            if s.enum == sp:
                ret = s
                break
        else:
            ret = None
        return ret


class VNXDomainNodeList(VNXCliResourceList):
    @classmethod
    def get_resource_class(cls):
        return VNXDomainNode

    def _get_raw_resource(self):
        return self._cli.get_domain(poll=self.poll)

    def get_node(self, node_id):
        for node in self:
            if node.name == node_id:
                ret = node
                break
        else:
            log.info('node "{}" not found in the vnx domain.'.format(node_id))
            ret = None
        return ret

    @staticmethod
    def get_cs_ip(serial, cli):
        dnl = VNXDomainNodeList(cli)
        dnl.with_no_poll()
        node = dnl.get_node(serial)
        if node is None or node.control_station is None:
            log.info('system {} does not has control station.'.format(serial))
            ret = None
        else:
            ret = node.control_station.ip_address
        return ret


class VNXDomainNode(VNXCliResource):
    @property
    def name(self):
        return self.node

    @property
    def spa(self):
        return self.members.spa

    @property
    def spb(self):
        return self.members.spb

    @property
    def control_station(self):
        return self.members.control_station


class VNXDomainMemberList(VNXCliResourceList):
    def _get_member(self, index):
        def filter_by_sp_name(member):
            sp = VNXSPEnum.parse(member.name)
            return sp == index

        result = filter(filter_by_sp_name, self.list)
        ret = None
        if len(result) > 0:
            ret = result[0]
        return ret

    @property
    def spa(self):
        return self._get_member(VNXSPEnum.SP_A)

    @property
    def spb(self):
        return self._get_member(VNXSPEnum.SP_B)

    @property
    def control_station(self):
        return self._get_member(VNXSPEnum.CONTROL_STATION)

    @classmethod
    def get_resource_class(cls):
        return VNXDomainMember

    def _get_raw_resource(self):
        return self._cli.get_domain()


class VNXDomainMember(VNXCliResource):
    @property
    def ip(self):
        ret = 'N/A'
        ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', self.ip_address)
        if len(ip) > 0:
            ret = ip[0]
        return ret

    @property
    def is_master(self):
        return 'Master' in self.ip_address

    def _get_raw_resource(self):
        raise NotImplementedError('cli does not support list domain member '
                                  'of a specified node.  '
                                  'please use VNXDomainNode instead.')


class VNXNetworkAdmin(VNXCliResource):
    def __init__(self, sp_index, cli):
        super(VNXNetworkAdmin, self).__init__()
        self._cli = cli
        self._sp = VNXSPEnum.parse(sp_index)

    def _get_raw_resource(self):
        return self._cli.sp_network_status(self._sp, poll=self.poll)

    @staticmethod
    def _get_sp_ip(sp, cli):
        sp = VNXNetworkAdmin(VNXSPEnum.parse(sp), cli)
        sp.with_no_poll()
        return sp.ip

    @classmethod
    def get_spa_ip(cls, cli):
        return cls._get_sp_ip(VNXSPEnum.SP_A, cli)

    @classmethod
    def get_spb_ip(cls, cli):
        return cls._get_sp_ip(VNXSPEnum.SP_B, cli)
