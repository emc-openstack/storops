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

from storops.lib.common import instance_cache, clear_instance_cache
from storops.vnx.resource import VNXCliResource, VNXCliResourceList
from storops.vnx.resource.sg import VNXStorageGroupList

__author__ = 'Cedric Zhuang'


class VNXHost(VNXCliResource):
    def __init__(self, name=None, cli=None):
        super(VNXHost, self).__init__()
        self._cli = cli
        self._name = name

        self.name = self._name
        self.connections = None
        self.storage_group = None
        self._existed = False

    def property_names(self):
        return ['name', 'connections', 'lun_list', 'alu_hlu_map']

    def get_index(self):
        return 'name'

    @property
    @instance_cache
    def lun_list(self):
        return self.storage_group.lun_list

    @property
    @instance_cache
    def alu_hlu_map(self):
        return self.storage_group.get_alu_hlu_map()

    @property
    def alu_ids(self):
        if self.alu_hlu_map is not None:
            ret = self.alu_hlu_map.keys()
        else:
            ret = tuple()
        return ret

    @property
    def hlu_ids(self):
        if self.alu_hlu_map is not None:
            ret = self.alu_hlu_map.values()
        else:
            ret = tuple()
        return ret

    @clear_instance_cache
    def update(self, data=None):
        host_list = VNXHostList(cli=self._cli)
        for host in host_list:
            if host.name == self._name:
                self._existed = True
                self.name = host.name
                self.connections = host.connections
                self.storage_group = host.storage_group
        return self

    @property
    def existed(self):
        return self._existed

    @classmethod
    def get(cls, cli, name=None):
        if name is None:
            ret = VNXHostList(cli)
        else:
            ret = VNXHost(cli=cli, name=name).update()
        return ret


class VNXHostList(VNXCliResourceList):
    def __init__(self, cli=None, names=None):
        super(VNXHostList, self).__init__()
        self._cli = cli
        self._names = names

    @classmethod
    def get_resource_class(cls):
        return VNXHost

    def update(self, data=None):
        sg_list = VNXStorageGroupList(cli=self._cli, engineering=True)
        hosts = []
        host_names = []
        for sg in sg_list:
            if sg.hba_sp_pairs:
                for pair in sg.hba_sp_pairs:
                    name = pair.host_name
                    if self._names is not None and name not in self._names:
                        continue

                    if name in host_names:
                        host = hosts[host_names.index(name)]
                    else:
                        host = VNXHost(name=name, cli=self._cli)
                        host.connections = []
                        host.storage_group = sg
                        hosts.append(host)
                        host_names.append(name)

                    host.connections.append(pair)
        self._list = hosts
        return self
