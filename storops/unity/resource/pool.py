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
import bitmath

from storops.unity.resource import UnityResource, \
    UnityAttributeResource, UnityResourceList
import storops.unity.resource.filesystem
from storops.unity.resource.lun import UnityLun

__author__ = 'Jay Xu'

LOG = logging.getLogger(__name__)


class UnityPool(UnityResource):
    def create_filesystem(self, nas_server, name, size,
                          proto=None, is_thin=None, tiering_policy=None):
        clz = storops.unity.resource.filesystem.UnityFileSystem
        return clz.create(self._cli, self,
                          nas_server=nas_server,
                          name=name,
                          size=size,
                          proto=proto,
                          is_thin=is_thin,
                          tiering_policy=tiering_policy)

    def create_lun(self, lun_name=None, size_gb=1, sp=None, host_access=None,
                   is_thin=None, description=None, tiering_policy=None,
                   is_repl_dst=None, snap_schedule=None, io_limit_policy=None):
        size = int(bitmath.GiB(size_gb).to_Byte().value)
        return UnityLun.create(self._cli, lun_name, self, size, sp=sp,
                               host_access=host_access, is_thin=is_thin,
                               description=description,
                               is_repl_dst=is_repl_dst,
                               tiering_policy=tiering_policy,
                               snap_schedule=snap_schedule,
                               io_limit_policy=io_limit_policy)

    def create_nfs_share(self, nas_server, name, size, is_thin=None,
                         tiering_policy=None):
        clz = storops.unity.resource.job.UnityJob
        return clz.create_nfs_share(
            self._cli, self, nas_server, name, size,
            is_thin, tiering_policy, False)


class UnityPoolList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityPool


class UnityPoolTier(UnityAttributeResource):
    pass


class UnityPoolTierList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityPoolTier


class UnityPoolUnit(UnityResource):
    pass


class UnityPoolUnitList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityPoolUnit


class UnityPoolFastVp(UnityAttributeResource):
    pass
