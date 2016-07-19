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

import storops.unity.resource.nas_server
import storops.unity.resource.pool
from storops.unity.enums import NodeEnum
from storops.unity.resource import UnityResource, UnityResourceList

__author__ = 'Jay Xu, Cedric Zhuang'

LOG = logging.getLogger(__name__)


class UnityStorageProcessor(UnityResource):
    def create_nas_server(self, name, pool=None, is_repl_dst=None,
                          multi_proto=None, tenant=None):
        if pool is None:
            pool_list_clz = storops.unity.resource.pool.UnityPoolList
            pool = self._get_unity_rsc(pool_list_clz).first_item
        nas_server_clz = storops.unity.resource.nas_server.UnityNasServer
        return nas_server_clz.create(self._cli, name, self, pool,
                                     is_repl_dst=is_repl_dst,
                                     multi_proto=multi_proto,
                                     tenant=tenant)

    def to_node_enum(self):
        if self.name in ['SP A']:
            value = 0
        elif self.name in ['SP B']:
            value = 1
        else:
            # NodeEnum.Unknown
            value = 2989
        return NodeEnum.parse(value)


class UnityStorageProcessorList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityStorageProcessor
