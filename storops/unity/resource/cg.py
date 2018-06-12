# Copyright (c) 2018 Dell Inc. or its subsidiaries.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from __future__ import unicode_literals

from storops import HostLUNAccessEnum
from storops.exception import UnityStorageResourceNameInUseError, \
    UnityConsistencyGroupNameInUseError
from storops.unity import enums
from storops.unity.resource import lun as lun_mod
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.snap import UnitySnap, UnitySnapList
from storops.unity.resource.storage_resource import UnityStorageResource, \
    UnityStorageResourceList
from storops.unity.resp import RESP_OK

__author__ = 'Peter Wang'

import logging

log = logging.getLogger(__name__)


class UnityConsistencyGroup(UnityStorageResource):
    """
    Create a consistency group (former LUN group).
    """

    @classmethod
    def create(cls, cli, name, description=None, is_repl_dst=None,
               snap_schedule=None, tiering_policy=None,
               is_compression=None,
               hosts=None, lun_add=None):
        req_body = cls._compose_cg_parameters(cli, name, description,
                                              is_repl_dst,
                                              snap_schedule, tiering_policy,
                                              is_compression,
                                              hosts,
                                              lun_add)
        resp = cli.type_action(UnityStorageResource().resource_class,
                               'createConsistencyGroup', **req_body)
        try:
            resp.raise_if_err()
        except UnityStorageResourceNameInUseError:
            raise UnityConsistencyGroupNameInUseError()
        except:  # noqa
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

    def modify(self, name=None, description=None, is_repl_dst=None,
               snap_schedule=None, tiering_policy=None,
               is_compression=None, hosts=None,
               lun_add=None, lun_remove=None, host_add=None,
               host_remove=None, lun_modify=None):
        req_body = self._compose_cg_parameters(
            self._cli, name, description,
            is_repl_dst, snap_schedule, tiering_policy,
            is_compression, hosts,
            lun_add, lun_remove, host_add, host_remove, lun_modify)
        resp = self._cli.action(UnityStorageResource().resource_class,
                                self.get_id(), 'modifyConsistencyGroup',
                                **req_body)
        resp.raise_if_err()
        return resp

    @staticmethod
    def _compose_cg_parameters(cli, name=None, description=None,
                               is_repl_dst=None,
                               snap_schedule=None, tiering_policy=None,
                               is_compression=None,
                               hosts=None,
                               lun_add=None,
                               lun_remove=None,
                               host_add=None,
                               host_remove=None,
                               lun_modify=None):
        host_access = UnityConsistencyGroup._wrap_host_list(hosts, cli)
        host_access_add = UnityConsistencyGroup._wrap_host_list(host_add, cli)

        lun_add = UnityConsistencyGroup._wrap_lun_list(lun_add)
        lun_remove = UnityConsistencyGroup._wrap_lun_list(lun_remove)

        req_body = cli.make_body(
            name=name,
            description=description,
            replicationParameters=cli.make_body(
                isReplicationDestination=is_repl_dst),
            fastVPParameters=cli.make_body(
                tieringPolicy=tiering_policy),
            dataReductionParameters=cli.make_body(
                isDataReductionEnabled=is_compression
            ),
            snapScheduleParameters=cli.make_body(
                snapSchedule=snap_schedule
            ),
            blockHostAccess=cli.make_body(host_access),
            lunAdd=cli.make_body(lun_add),
            lunRemove=cli.make_body(lun_remove),
            addBlockHostAccess=cli.make_body(host_access_add),
            removeBlockHostAccess=cli.make_body(host_remove),
        )
        # Empty host access can be used to wipe the host_access
        if lun_modify is not None:
            lun_modify = cli.make_body(lun_modify, allow_empty=True)
            req_body['lunModify'] = lun_modify

        return req_body

    def modify_lun(self, lun, name=None, size=None, host_access=None,
                   description=None, sp=None, io_limit_policy=None,
                   tiering_policy=None, is_compression=None):

        lun_modify = self._cli.make_body(lun=lun,
                                         name=name,
                                         description=description)
        # `hostAccess` could be empty list which is used to remove all host
        # access
        lun_parameters = lun_mod.prepare_lun_parameters(
            cli=self._cli,
            size=size,
            host_access=host_access,
            sp=sp,
            io_limit_policy=io_limit_policy,
            tiering_policy=tiering_policy,
            is_compression=is_compression)
        if lun_parameters:
            lun_modify['lunParameters'] = lun_parameters

        return self.modify(lun_modify=[lun_modify])

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

    @staticmethod
    def _wrap_lun_list(lun_list):
        if lun_list is not None:
            ret = list(map(lambda lun: {'lun': lun}, lun_list))
        else:
            ret = None
        return ret

    def add_lun(self, *lun_list):
        return self.modify(lun_add=lun_list)

    def remove_lun(self, *lun_list):
        return self.modify(lun_remove=lun_list)

    @property
    def existing_lun_ids(self):
        luns = self.luns if self.luns else []
        return {lun.get_id() for lun in luns}

    def _prepare_luns_add(self, lun_list):
        if not lun_list:
            return None
        add_ids = {lun.get_id() for lun in lun_list} - self.existing_lun_ids
        log.debug("Adding LUN(s) '{}' to cg {}".format(add_ids, self.get_id()))
        return [UnityLun(_id=_id, cli=self._cli) for _id in add_ids]

    def _prepare_luns_remove(self, lun_list, is_delta):
        if not lun_list:
            return None
        lun_ids = {lun.get_id() for lun in lun_list}
        if is_delta:
            remove_ids = self.existing_lun_ids & lun_ids
        else:
            remove_ids = self.existing_lun_ids - lun_ids
        log.debug("Removing LUN(s) '{}' from cg '{}'".format(remove_ids,
                                                             self.get_id()))
        return [UnityLun(_id=_id, cli=self._cli) for _id in remove_ids]

    def replace_lun(self, *lun_list):
        """Replaces the exiting LUNs to lun_list."""
        lun_add = self._prepare_luns_add(lun_list)
        lun_remove = self._prepare_luns_remove(lun_list, False)
        return self.modify(lun_add=lun_add, lun_remove=lun_remove)

    def update_lun(self, add_luns=None, remove_luns=None):
        """Updates the LUNs in CG, adding the ones in `add_luns` and removing
        the ones in `remove_luns`"""
        if not add_luns and not remove_luns:
            log.debug("Empty add_luns and remove_luns passed in, "
                      "skip update_lun.")
            return RESP_OK
        lun_add = self._prepare_luns_add(add_luns)
        lun_remove = self._prepare_luns_remove(remove_luns, True)
        return self.modify(lun_add=lun_add, lun_remove=lun_remove)

    def attach_to(self, host=None, access_mask=HostLUNAccessEnum.BOTH):
        """Attaches all member LUNs to the specified host."""
        raise NotImplementedError()

    def detach_from(self, host=None):
        """Detaches all members from host, if None, detach from all hosts."""
        raise NotImplementedError()

    def set_host_access(self, *hosts):
        return self.modify(hosts=hosts)

    def add_host_access(self, *hosts):
        return self.modify(host_add=hosts)

    def remove_host_access(self, *hosts):
        return self.modify(host_remove=hosts)

    def create_snap(self, name=None, description=None, is_auto_delete=None,
                    retention_duration=None):
        clz = UnitySnap
        return clz.create(self._cli, self, name=name, description=description,
                          is_auto_delete=is_auto_delete,
                          retention_duration=retention_duration,
                          is_read_only=None, fs_access_type=None)

    @property
    def snapshots(self):
        clz = UnitySnapList
        snaps = clz(cli=self._cli, storage_resource=self)
        return list(filter(lambda snap: snap.snap_group is None, snaps))


class UnityConsistencyGroupList(UnityStorageResourceList):
    type_cg = enums.StorageResourceTypeEnum.CONSISTENCY_GROUP

    def __init__(self, **the_filter):
        the_filter['type'] = self.type_cg
        super(UnityConsistencyGroupList, self).__init__(**the_filter)

    @classmethod
    def get_resource_class(cls):
        return UnityConsistencyGroup

    def _filter(self, item):
        return item.type == self.type_cg
