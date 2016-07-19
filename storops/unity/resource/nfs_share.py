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

from storops.exception import UnityShareTypeNotSupportAccessControlError, \
    UnityHostNotFoundException, UnityCreateSnapError
from storops.lib.common import instance_cache
from storops.unity.enums import NFSShareDefaultAccessEnum, NFSTypeEnum, \
    NFSShareSecurityEnum, FilesystemSnapAccessTypeEnum
import storops.unity.resource.filesystem
import storops.unity.resource.snap
from storops.unity.resource import UnityResource, UnityResourceList
import storops.unity.resource.host
from storops.unity.resp import RestResponse

__author__ = 'Jay Xu'

LOG = logging.getLogger(__name__)


class UnityNfsHostConfig(object):
    def __init__(self, root=None, ro=None, rw=None, no_access=None,
                 nfs_share=None):
        if nfs_share is not None:
            root = nfs_share.root_access_hosts
            ro = nfs_share.read_only_hosts
            rw = nfs_share.read_write_hosts
            no_access = nfs_share.no_access_hosts

        self.root = root
        self.ro = ro
        self.rw = rw
        self.no_access = no_access

    @classmethod
    def _add(cls, left, right):
        if left is None:
            ret = right
        elif right is None:
            ret = left
        else:
            ret = left
            for r in right:
                if r not in left:
                    ret.append(r)
        return ret

    @classmethod
    def _delete(cls, left, right):
        if left is None:
            ret = None
        elif right is None:
            ret = left
        else:
            ret = []
            for l in left:
                if l not in right:
                    ret.append(l)
        return ret

    def allow_root(self, *hosts):
        self.delete_access(*hosts)
        self.root = self._add(self.root, hosts)
        return self

    def allow_ro(self, *hosts):
        self.delete_access(*hosts)
        self.ro = self._add(self.ro, hosts)
        self.root = self._add(self.root, hosts)
        return self

    def allow_rw(self, *hosts):
        self.delete_access(*hosts)
        self.rw = self._add(self.rw, hosts)
        self.root = self._add(self.root, hosts)
        return self

    def deny_access(self, *hosts):
        self.delete_access(*hosts)
        self.no_access = self._add(self.no_access, hosts)
        return self

    def delete_access(self, *hosts):
        self.rw = self._delete(self.rw, hosts)
        self.ro = self._delete(self.ro, hosts)
        self.no_access = self._delete(self.no_access, hosts)
        self.root = self._delete(self.root, hosts)
        return self

    @staticmethod
    def _inter(left, right):
        if left is None:
            left = []
        right_ids = [host.get_id() for host in right]
        return [host for host in left if host.get_id() in right_ids]

    def clear_all(self, *white_list_hosts):
        self.rw = self._inter(self.rw, white_list_hosts)
        self.ro = self._inter(self.ro, white_list_hosts)
        self.no_access = self._inter(self.no_access, white_list_hosts)
        self.root = self._inter(self.root, white_list_hosts)
        return self


class UnityNfsShare(UnityResource):
    @classmethod
    def create(cls, cli, name, fs, path=None, share_access=None):
        fs_clz = storops.unity.resource.filesystem.UnityFileSystem
        fs = fs_clz.get(cli, fs).verify()
        NFSShareDefaultAccessEnum.verify(share_access)
        sr = fs.storage_resource

        if path is None:
            path = '/'

        share_param = cli.make_body(defaultAccess=share_access)
        param = cli.make_body(name=name, path=path,
                              nfsShareParameters=share_param)
        resp = sr.modify_fs(nfsShareCreate=[param])
        resp.raise_if_err()
        return UnityNfsShareList(cli=cli, name=name).first_item

    @classmethod
    def create_from_snap(cls, cli, snap, name, path=None, is_read_only=None,
                         default_access=None):
        snap_clz = storops.unity.resource.snap.UnitySnap
        snap = snap_clz.get(cli, snap)
        NFSShareDefaultAccessEnum.verify(default_access)

        if path is None:
            path = '/'

        resp = cli.post(cls().resource_class,
                        snap=snap,
                        path=path,
                        name=name,
                        isReadOnly=is_read_only,
                        defaultAccess=default_access)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def delete(self, async=False):
        if self.type == NFSTypeEnum.NFS_SNAPSHOT:
            resp = super(UnityNfsShare, self).delete(async=async)
        else:
            fs = self.filesystem.verify()
            sr = fs.storage_resource
            param = self._cli.make_body(nfsShare=self)
            resp = sr.modify_fs(async=async, nfsShareDelete=[param])
        resp.raise_if_err()
        return resp

    def _get_hosts(self, hosts, force_create_host=False):
        if not isinstance(hosts, (tuple, list, set, UnityResourceList)):
            hosts = [hosts]
        host_clz = storops.unity.resource.host.UnityHost
        ret = []
        for item in hosts:
            host = host_clz.get_host(self._cli, item, force_create_host,
                                     tenant=self.tenant)
            if host is not None:
                ret.append(host)
        if hosts and len(ret) == 0:
            raise UnityHostNotFoundException()
        return ret

    @property
    def host_config(self):
        # host config must be up-to-date for each call!
        self.update()
        return UnityNfsHostConfig(nfs_share=self)

    def allow_root_access(self, hosts, force_create_host=False):
        hosts = self._get_hosts(hosts, force_create_host)
        config = self.host_config.allow_root(*hosts)
        return self.modify(host_config=config)

    def allow_read_only_access(self, hosts, force_create_host=False):
        hosts = self._get_hosts(hosts, force_create_host)
        config = self.host_config.allow_ro(*hosts)
        return self.modify(host_config=config)

    def allow_read_write_access(self, hosts, force_create_host=False):
        hosts = self._get_hosts(hosts, force_create_host)
        config = self.host_config.allow_rw(*hosts)
        return self.modify(host_config=config)

    def deny_access(self, hosts, force_create_host=False):
        hosts = self._get_hosts(hosts, force_create_host)
        config = self.host_config.deny_access(*hosts)
        return self.modify(host_config=config)

    def delete_access(self, hosts):
        hosts = self._get_hosts(hosts)
        config = self.host_config.delete_access(*hosts)
        return self.modify(host_config=config)

    def clear_access(self, white_list=None, force_create_host=False):
        if white_list is not None:
            white_list = self._get_hosts(white_list, force_create_host)
        else:
            white_list = []
        config = self.host_config.clear_all(*white_list)
        return self.modify(host_config=config)

    def modify(self,
               default_access=None,
               min_security=None,
               no_access_hosts=None,
               read_only_hosts=None,
               read_write_hosts=None,
               root_access_hosts=None,
               host_config=None):
        if host_config is not None:
            no_access_hosts = host_config.no_access
            root_access_hosts = host_config.root
            read_only_hosts = host_config.ro
            read_write_hosts = host_config.rw

        NFSShareDefaultAccessEnum.verify(default_access)
        NFSShareSecurityEnum.verify(min_security)
        clz = storops.unity.resource.host.UnityHostList
        no_access_hosts = clz.get_list(self._cli, no_access_hosts)
        read_only_hosts = clz.get_list(self._cli, read_only_hosts)
        read_write_hosts = clz.get_list(self._cli, read_write_hosts)
        root_access_hosts = clz.get_list(self._cli, root_access_hosts)

        nfs_share_param = self._cli.make_body(
            allow_empty=True,
            defaultAccess=default_access,
            minSecurity=min_security,
            noAccessHosts=no_access_hosts,
            readOnlyHosts=read_only_hosts,
            readWriteHosts=read_write_hosts,
            rootAccessHosts=root_access_hosts)

        if nfs_share_param:
            # different api for different type of share
            if self.type == NFSTypeEnum.NFS_SHARE:
                resp = self._modify_fs_share(nfs_share_param)
            elif self.type == NFSTypeEnum.NFS_SNAPSHOT:
                resp = self._modify_snap_share(default_access,
                                               min_security,
                                               nfs_share_param)
            else:
                raise UnityShareTypeNotSupportAccessControlError()
        else:
            resp = RestResponse('', self._cli)
        resp.raise_if_err()
        return resp

    def _modify_snap_share(self, default_access, min_security,
                           nfs_share_param):
        return self.action('modify',
                           defaultAccess=default_access,
                           minSecurity=min_security,
                           **nfs_share_param)

    def _modify_fs_share(self, nfs_share_param):
        sr = self.storage_resource
        if sr is None:
            raise ValueError('storage resource for share {} not found.'
                             .format(self.name))
        nfs_share = self._cli.make_body(
            allow_empty=True,
            nfsShare=self,
            nfsShareParameters=nfs_share_param)
        param = self._cli.make_body(
            allow_empty=True,
            nfsShareModify=[nfs_share])
        return sr.modify_fs(**param)

    @property
    @instance_cache
    def storage_resource(self):
        fs = self.filesystem
        if fs is not None:
            ret = fs.storage_resource
        else:
            ret = None
        return ret

    @property
    @instance_cache
    def tenant(self):
        if self.filesystem is not None:
            server = self.filesystem.nas_server
            if server is not None:
                return server.tenant
        return None

    def create_snap(self, name=None, fs_access_type=None):
        if fs_access_type is None:
            fs_access_type = FilesystemSnapAccessTypeEnum.PROTOCOL

        if self.type == NFSTypeEnum.NFS_SHARE:
            ret = self.filesystem.create_snap(
                name=name, fs_access_type=fs_access_type)
        elif self.type == NFSTypeEnum.NFS_SNAPSHOT:
            ret = self.snap.copy(copy_name=name)
        else:
            raise UnityCreateSnapError('do not know how to create snap for '
                                       'nfs share {}, type {}.'
                                       .format(self.name, self.type))
        return ret


class UnityNfsShareList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityNfsShare
