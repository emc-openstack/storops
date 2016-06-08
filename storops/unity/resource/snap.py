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

from storops.lib.common import instance_cache
from storops.unity.enums import FilesystemSnapAccessTypeEnum, SnapStateEnum
from storops.unity.resource import UnityResource, UnityResourceList
import storops.unity.resource.cifs_share
import storops.unity.resource.nfs_share
from storops.unity.resource.storage_resource import UnityStorageResource

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class UnitySnap(UnityResource):
    @classmethod
    def create(cls, cli, storage_resource, name=None,
               description=None, is_auto_delete=None,
               retention_duration=None, is_read_only=None,
               fs_access_type=None):
        FilesystemSnapAccessTypeEnum.verify(fs_access_type)
        sr = UnityStorageResource.get(cli, storage_resource)

        resp = cli.post(cls().resource_class,
                        storageResource=sr,
                        name=name,
                        description=description,
                        isAutoDelete=is_auto_delete,
                        retentionDuration=retention_duration,
                        isReadOnly=is_read_only,
                        filesystemAccessType=fs_access_type)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def create_cifs_share(self, name, path=None, is_read_only=None):
        clz = storops.unity.resource.cifs_share.UnityCifsShare
        return clz.create_from_snap(
            self._cli, snap=self, name=name, path=path,
            is_read_only=is_read_only)

    def create_nfs_share(self, name, path=None, is_read_only=None,
                         default_access=None):
        clz = storops.unity.resource.nfs_share.UnityNfsShare
        return clz.create_from_snap(
            self._cli, snap=self, name=name, path=path,
            is_read_only=is_read_only, default_access=default_access)

    def create_snap(self, name=None,
                    description=None, is_auto_delete=None,
                    retention_duration=None, is_read_only=None,
                    fs_access_type=None):
        return self.create(cli=self._cli,
                           storage_resource=self.storage_resource,
                           name=name,
                           description=description,
                           is_auto_delete=is_auto_delete,
                           retention_duration=retention_duration,
                           is_read_only=is_read_only,
                           fs_access_type=fs_access_type)

    def copy(self, copy_name=None):
        resp = self.action('copy', copyName=copy_name)
        resp.raise_if_err()
        try:
            snap_copy_id = resp.contents[0]['copies'][0]['id']
            ret = self.get(self._cli, snap_copy_id)
        except (IndexError, KeyError, TypeError):
            log.exception('failed to get snap id from resp: {}'.format(resp))
            raise
        return ret

    @property
    @instance_cache
    def filesystem(self):
        sr = self.storage_resource
        if sr:
            ret = sr.filesystem
        else:
            ret = None
        return ret

    @property
    def existed(self):
        return (super(UnitySnap, self).existed and
                self.state != SnapStateEnum.DESTROYING)


class UnitySnapList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySnap


class UnitySnapSchedule(UnityResource):
    pass


class UnitySnapScheduleList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySnapSchedule


class UnitySnapScheduleRule(UnityResource):
    pass


class UnitySnapScheduleRuleList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySnapScheduleRule
