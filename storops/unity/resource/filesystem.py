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

from storops.lib.common import supplement_filesystem
from storops.exception import UnityResourceNotFoundError, \
    UnityCifsServiceNotEnabledError, UnityShareShrinkSizeTooLargeError, \
    UnityShareShrinkSizeTooSmallError, UnityLocalReplicationFsNameNotSameError
from storops.unity.enums import FSSupportedProtocolEnum, TieringPolicyEnum, \
    SnapStateEnum

import storops.unity.resource.nas_server
import storops.unity.resource.pool
import storops.unity.resource.nfs_share
import storops.unity.resource.cifs_share
from storops.unity.resource import UnityResource, UnityResourceList
from storops.unity.resource.replication_session import \
    UnityReplicationSession, UnityResourceConfig
from storops.unity.resource.snap import UnitySnap, UnitySnapList
from storops.unity.resource.storage_resource import UnityStorageResource

__author__ = 'Jay Xu'

log = logging.getLogger(__name__)


class UnityFileSystem(UnityResource):
    @classmethod
    def create(cls, cli, pool, nas_server, name, size,
               proto=None, is_thin=None,
               tiering_policy=None, user_cap=False):
        pool_clz = storops.unity.resource.pool.UnityPool
        nas_server_clz = storops.unity.resource.nas_server.UnityNasServer

        if proto is None:
            proto = FSSupportedProtocolEnum.NFS

        pool = pool_clz.get(cli, pool)
        nas_server = nas_server_clz.get(cli, nas_server)
        FSSupportedProtocolEnum.verify(proto)
        TieringPolicyEnum.verify(tiering_policy)
        size = supplement_filesystem(size, user_cap)

        req_body = {
            'name': name,
            'fsParameters': {
                'pool': pool,
                'nasServer': nas_server,
                'supportedProtocols': proto,
                'isThinEnabled': is_thin,
                'size': size,
                'fastVPParameters': {
                    'tieringPolicy': tiering_policy
                }
            },
        }
        resp = cli.type_action(UnityStorageResource().resource_class,
                               'createFilesystem',
                               **req_body)
        resp.raise_if_err()
        sr = UnityStorageResource(_id=resp.resource_id, cli=cli)
        return sr.filesystem

    @property
    def first_available_cifs_server(self):
        ret = None
        if self.nas_server is not None:
            try:
                ret = self.nas_server.get_cifs_server()
            except UnityCifsServiceNotEnabledError as e:
                log.info(e.message)
        return ret

    def delete(self, force_snap_delete=False, force_vvol_delete=False,
               async_mode=False):
        sr = self.storage_resource
        if not self.existed or sr is None:
            raise UnityResourceNotFoundError(
                'cannot find filesystem {}.'.format(self.get_id()))
        resp = self._cli.delete(sr.resource_class,
                                sr.get_id(),
                                forceSnapDeletion=force_snap_delete,
                                forceVvolDeletion=force_vvol_delete,
                                async_mode=async_mode)
        resp.raise_if_err()
        return resp

    def extend(self, new_size, user_cap=False):
        sr = self.storage_resource
        new_size = supplement_filesystem(new_size, user_cap)
        param = self._cli.make_body(size=new_size)
        resp = sr.modify_fs(fsParameters=param)
        resp.raise_if_err()
        return resp

    def shrink(self, new_size, user_cap=False):
        sr = self.storage_resource
        new_size = supplement_filesystem(new_size, user_cap)
        size_used = sr.size_used
        if size_used and int(size_used) > new_size:
            message = 'Reject shrink share request, ' \
                      'the new size should be larger than used.'
            raise UnityShareShrinkSizeTooSmallError(message)
        param = self._cli.make_body(size=new_size)
        size_total = sr.size_total
        if size_total and int(size_total) < new_size:
            message = 'Reject shrink share request, ' \
                      'the new size should be smaller than original.'
            raise UnityShareShrinkSizeTooLargeError(message)
        resp = sr.modify_fs(fsParameters=param)
        resp.raise_if_err()
        return resp

    def create_nfs_share(self, name, path=None, share_access=None):
        clz = storops.unity.resource.nfs_share.UnityNfsShare
        return clz.create(self._cli, name=name, fs=self,
                          path=path, share_access=share_access)

    def create_cifs_share(self, name, path=None, cifs_server=None):
        clz = storops.unity.resource.cifs_share.UnityCifsShare
        return clz.create(self._cli, name=name, fs=self,
                          path=path, cifs_server=cifs_server)

    def create_snap(self, name=None,
                    description=None, is_auto_delete=None,
                    retention_duration=None, is_read_only=None,
                    fs_access_type=None):
        return UnitySnap.create(cli=self._cli,
                                storage_resource=self.storage_resource,
                                name=name,
                                description=description,
                                is_auto_delete=is_auto_delete,
                                retention_duration=retention_duration,
                                is_read_only=is_read_only,
                                fs_access_type=fs_access_type)

    @property
    def snapshots(self):
        return UnitySnapList(cli=self._cli,
                             storage_resource=self.storage_resource)

    def has_snap(self, ignore_system_snap=False):
        """ This method won't count the snaps in "destroying" state!

        :param ignore_system_snap: ignore the system snap if True.
        :return: false if no snaps or all snaps are destroying.
        """
        snaps = filter(lambda s: s.state != SnapStateEnum.DESTROYING,
                       self.snapshots)
        if ignore_system_snap:
            snaps = filter(lambda s: not s.is_system_snap, snaps)
        return len(list(snaps)) > 0

    def replicate_with_dst_resource_provisioning(self, max_time_out_of_sync,
                                                 dst_pool_id,
                                                 dst_fs_name=None,
                                                 remote_system=None,
                                                 replication_name=None,
                                                 dst_size=None,
                                                 is_dst_thin=None,
                                                 dst_tiering_policy=None,
                                                 is_dst_compression=None):
        """
        Creates a replication session with destination filesystem provisioning.

        :param max_time_out_of_sync: maximum time to wait before syncing the
            source and destination. Value `-1` means the automatic sync is not
            performed. `0` means it is a sync replication.
        :param dst_pool_id: id of pool to allocate destination filesystem.
        :param dst_fs_name: destination filesystem name. If `remote_system` is
            `None` (for local replication creation), `dst_fs_name` should be
            same as the source fs name or `None`.
        :param remote_system: `UnityRemoteSystem` object. The remote system to
            which the replication is being configured. When not specified, it
            defaults to local system.
        :param replication_name: replication name.
        :param dst_size: destination filesystem size.
        :param is_dst_thin: indicates whether destination filesystem is thin or
            not.
        :param dst_tiering_policy: `TieringPolicyEnum` value. Tiering policy of
            destination filesystem.
        :param is_dst_compression: indicates whether destination filesystem is
            compression enabled or not.
        :return: created replication session.
        """

        if dst_fs_name is None:
            dst_fs_name = self.name
        if remote_system is None and dst_fs_name != self.name:
            raise UnityLocalReplicationFsNameNotSameError(
                'dst_fs_name passed in for creating filesystem local '
                'replication should be same as source filesystem name '
                'or None')

        dst_size = self.size_total if dst_size is None else dst_size

        dst_resource = UnityResourceConfig.to_embedded(
            name=dst_fs_name, pool_id=dst_pool_id, size=dst_size,
            tiering_policy=dst_tiering_policy, is_thin_enabled=is_dst_thin,
            is_compression_enabled=is_dst_compression)
        return UnityReplicationSession.create_with_dst_resource_provisioning(
            self._cli, self.storage_resource.get_id(),
            dst_resource, max_time_out_of_sync,
            remote_system=remote_system, name=replication_name)


class UnityFileSystemList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityFileSystem
