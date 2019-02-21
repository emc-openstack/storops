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

__author__ = 'Yong Huang'

LOG = logging.getLogger(__name__)


class UnityMigrationObject(UnityResource):
    @classmethod
    def discover(cls, cli, remote_system):
        """
        Discover migrationObject instances on the remoteSystem.

        :param remote_system: Remote system from which objects need to
            be migrated.
        :return:
        """

        req_body = cli.make_body(remoteSystem=remote_system)
        resp = cli.type_action(cls().resource_class, 'discover', **req_body)
        resp.raise_if_err()
        return resp


class UnityMigrationObjectList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityMigrationObject


class UnityLunInfo(UnityResource):
    pass


class UnityLunInfoList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityLunInfo


class UnityFilesystemInfo(UnityResource):
    pass


class UnityFilesystemInfoList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityFilesystemInfo


class UnityInterfaceInfo(UnityResource):
    pass


class UnityInterfaceInfoList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityInterfaceInfo


class UnityCifsServerInfo(UnityResource):
    pass


class UnityCifsServerInfoList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityCifsServerInfo


class UnityVdmInfo(UnityResource):
    pass


class UnityVdmInfoList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityVdmInfo
