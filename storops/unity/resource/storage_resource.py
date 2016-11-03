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

from storops.exception import UnityStorageResourceNameInUseError, \
    UnityConsistencyGroupNameInUseError
from storops.unity import enums
from storops.unity.resource import UnityResource, UnityResourceList
import storops.unity.resource.snap

__author__ = 'Cedric Zhuang'


class UnityStorageResource(UnityResource):
    @classmethod
    def get(cls, cli, _id=None):
        if not isinstance(_id, (cls, UnityConsistencyGroup)):
            ret = cls(_id=_id, cli=cli)
        else:
            ret = _id
        return ret

    def action(self, action_name, **kwargs):
        return self._cli.action(self.resource_class,
                                self.get_id(),
                                action_name,
                                **kwargs)

    def modify_fs(self, **kwargs):
        return self.action('modifyFilesystem', **kwargs)


class UnityStorageResourceList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityStorageResource


class UnityConsistencyGroup(UnityResource):
    @classmethod
    def create(cls, cli, name, description=None, lun_list=None,
               hosts=None):
        lun_list = cls._wrap_lun_list(lun_list)
        hosts = cls._wrap_host_list(hosts, cli)

        req_body = cli.make_body(name=name,
                                 description=description,
                                 lunAdd=lun_list,
                                 blockHostAccess=hosts)
        resp = cli.type_action(UnityStorageResource().resource_class,
                               'createConsistencyGroup', **req_body)

        try:
            resp.raise_if_err()
        except UnityStorageResourceNameInUseError:
            raise UnityConsistencyGroupNameInUseError()
        except:
            raise

        return UnityConsistencyGroup(_id=resp.resource_id, cli=cli)

    @property
    def name(self):
        if hasattr(self, '_name') and self._name is not None:
            name = self._name
        else:
            if not self._is_updated():
                self.update()
            name = self._get_value_by_key('name')
        return name

    @name.setter
    def name(self, new_name):
        self.modify(name=new_name)

    @staticmethod
    def _wrap_lun_list(lun_list):
        if lun_list is not None:
            ret = list(map(lambda lun: {'lun': lun}, lun_list))
        else:
            ret = None
        return ret

    @staticmethod
    def _wrap_host_list(host_list, cli):
        def make_host_elem(host):
            return cli.make_body(host=host,
                                 accessMask=enums.HostLUNAccessEnum.BOTH)

        if host_list is not None:
            ret = list(map(make_host_elem, host_list))
        else:
            ret = None
        return ret

    def add_lun(self, *lun_list):
        return self.modify(luns_to_add=lun_list)

    def remove_lun(self, *lun_list):
        return self.modify(luns_to_remove=lun_list)

    def set_host_access(self, *hosts):
        return self.modify(hosts=hosts)

    def add_host_access(self, *hosts):
        return self.modify(hosts_to_add=hosts)

    def remove_host_access(self, *hosts):
        return self.modify(hosts_to_remove=hosts)

    def create_snap(self, name=None, description=None, is_auto_delete=None,
                    retention_duration=None):
        clz = storops.unity.resource.snap.UnitySnap
        return clz.create(self._cli, self, name=name, description=description,
                          is_auto_delete=is_auto_delete,
                          retention_duration=retention_duration,
                          is_read_only=None, fs_access_type=None)

    @property
    def snapshots(self):
        clz = storops.unity.resource.snap.UnitySnapList
        snaps = clz(cli=self._cli, storage_resource=self)
        return list(filter(lambda snap: snap.snap_group is None, snaps))

    def modify(self, name=None, description=None,
               luns_to_add=None, luns_to_remove=None,
               hosts_to_add=None, hosts_to_remove=None, hosts=None):
        luns_to_add = self._wrap_lun_list(luns_to_add)
        luns_to_remove = self._wrap_lun_list(luns_to_remove)

        hosts_to_add = self._wrap_host_list(hosts_to_add, self._cli)
        hosts = self._wrap_host_list(hosts, self._cli)

        resp = self.action(
            'modifyConsistencyGroup',
            name=name, description=description,
            lunAdd=luns_to_add, lunRemove=luns_to_remove,
            blockHostAccess=hosts, addBlockHostAccess=hosts_to_add,
            removeBlockHostAccess=hosts_to_remove)
        resp.raise_if_err()
        return resp


class UnityConsistencyGroupList(UnityResourceList):
    type_cg = enums.StorageResourceTypeEnum.CONSISTENCY_GROUP

    def __init__(self, **the_filter):
        the_filter['type'] = self.type_cg
        super(UnityConsistencyGroupList, self).__init__(**the_filter)

    @classmethod
    def get_resource_class(cls):
        return UnityConsistencyGroup

    def _filter(self, item):
        return item.type == self.type_cg
