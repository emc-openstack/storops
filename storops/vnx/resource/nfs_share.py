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

from storops.vnx import xmlapi
from storops.vnx.resource.fs import VNXFileSystem
from storops.vnx.resource.mover import VNXMover
from storops.vnx.resource import VNXResource, VNXCliResourceList

__author__ = 'Jay Xu'

log = logging.getLogger(__name__)


class NfsHostConfig(object):
    def __init__(self, root_hosts=None, ro_hosts=None, rw_hosts=None,
                 access_hosts=None):
        self.root_hosts = root_hosts
        self.ro_hosts = ro_hosts
        self.rw_hosts = rw_hosts
        self.access_hosts = access_hosts

    def get_xml_node(self):
        xb = xmlapi.XmlBuilder()

        ret = []
        if self.access_hosts is not None:
            ret.append(xb.list_elements('AccessHosts', self.access_hosts))
        if self.rw_hosts is not None:
            ret.append(xb.list_elements('RwHosts', self.rw_hosts))
        if self.ro_hosts is not None:
            ret.append(xb.list_elements('RoHosts', self.ro_hosts))
        if self.root_hosts is not None:
            ret.append(xb.list_elements('RootHosts', self.root_hosts))
        return ret

    @staticmethod
    def _add(left, right):
        if left is None:
            left = []
        return list(set(left + list(right)))

    @staticmethod
    def _delete(left, right):
        if left is None:
            ret = None
        else:
            ret = set(left) - set(right)
        return ret

    def add_access_and_root_hosts(self, *hosts):
        self.root_hosts = self._add(self.root_hosts, hosts)
        self.access_hosts = self._add(self.access_hosts, hosts)

    def add_ro_hosts(self, *hosts):
        self.ro_hosts = self._add(self.ro_hosts, hosts)
        self.add_access_and_root_hosts(*hosts)

    def add_rw_hosts(self, *hosts):
        self.rw_hosts = self._add(self.rw_hosts, hosts)
        self.add_access_and_root_hosts(*hosts)

    def delete_hosts(self, *hosts):
        self.rw_hosts = self._delete(self.rw_hosts, hosts)
        self.ro_hosts = self._delete(self.ro_hosts, hosts)
        self.access_hosts = self._delete(self.access_hosts, hosts)
        self.root_hosts = self._delete(self.root_hosts, hosts)


class VNXNfsShareList(VNXCliResourceList):
    def __init__(self, cli=None, mover=None, path=None):
        super(VNXNfsShareList, self).__init__(cli)
        self._mover = mover
        self._path = path

    @classmethod
    def get_resource_class(cls):
        return VNXNfsShare

    def _get_raw_resource(self):
        if self._mover is not None:
            mover_id = VNXMover.get_id(self._mover)
        else:
            mover_id = None
        return self._cli.get_nfs_export(mover_id, self._path)


class VNXNfsShare(VNXResource):
    def __init__(self, mover=None, path=None, cli=None):
        super(VNXNfsShare, self).__init__()
        self._cli = cli
        self._mover = mover
        self._path = path

    def _get_raw_resource(self):
        if self._mover is not None:
            mover_id = VNXMover.get_id(self._mover)
        else:
            raise ValueError('mover for the nfs share is not specified.')
        if self._path is None:
            raise ValueError('path for the nfs share is not specified')
        return self._cli.get_nfs_export(mover_id, self._path)

    @staticmethod
    def get(cli, mover=None, path=None):
        if mover is not None and path is not None:
            ret = VNXNfsShare(mover=mover, path=path, cli=cli)
        else:
            ret = VNXNfsShareList(cli=cli, mover=mover, path=path)
        return ret

    @property
    def mover(self):
        if self._mover is not None:
            ret = self._mover
        else:
            ret = VNXMover(mover_id=self.mover_id, cli=self._cli)
        return ret

    @property
    def fs(self):
        return VNXFileSystem(fs_id=self.fs_id, cli=self._cli)

    def get_mover_id(self):
        return VNXMover.get_id(self._mover)

    @staticmethod
    def create(cli, mover, path, ro=False, host_config=None):
        mover_id = VNXMover.get_id(mover)
        resp = cli.create_nfs_export(mover_id, path, ro,
                                     host_config=host_config)
        resp.raise_if_err()
        return VNXNfsShare(cli=cli, mover=mover, path=path)

    def get_path(self):
        if self._path is not None:
            ret = self._path
        else:
            ret = self.path
        return ret

    def delete(self):
        mover_id = self.get_mover_id()
        resp = self._cli.delete_nfs_export(mover_id, self.get_path())
        resp.raise_if_err()
        return resp

    def modify(self, ro=None, host_config=None):
        mover_id = self.get_mover_id()
        path = self.get_path()
        resp = self._cli.modify_nfs_export(mover_id, path, ro, host_config)
        resp.raise_if_err()
        return resp

    @property
    def host_config(self):
        return NfsHostConfig(root_hosts=self.root_hosts,
                             ro_hosts=self.ro_hosts,
                             rw_hosts=self.rw_hosts,
                             access_hosts=self.access_hosts)

    def allow_ro_access(self, *hosts):
        host_config = self.host_config
        host_config.add_ro_hosts(*hosts)
        resp = self.modify(host_config=host_config)
        resp.raise_if_err()
        return resp

    def allow_rw_access(self, *hosts):
        host_config = self.host_config
        host_config.add_rw_hosts(*hosts)
        resp = self.modify(host_config=host_config)
        resp.raise_if_err()
        return resp

    def deny_access(self, *hosts):
        host_config = self.host_config
        host_config.delete_hosts(*hosts)
        resp = self.modify(host_config=host_config)
        resp.raise_if_err()
        return resp
