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
import storops.unity.resource.pool
from storops.unity.enums import TieringPolicyEnum, NodeEnum, HostLUNAccessEnum
from storops.unity.resource.storage_resource import UnityStorageResource
from storops.exception import UnityResourceNotFoundError
from storops.unity.resource.snap import UnitySnap, UnitySnapList
from storops.unity.resource.sp import UnityStorageProcessor

__author__ = 'Jay Xu'

log = logging.getLogger(__name__)


class UnityLun(UnityResource):
    @classmethod
    def create(cls, cli, name, pool, size, sp=None, host_access=None,
               is_thin=None, description=None, io_limit_policy=None,
               is_repl_dst=None, tiering_policy=None, snap_schedule=None):
        pool_clz = storops.unity.resource.pool.UnityPool
        pool = pool_clz.get(cli, pool)

        req_body = cls._compose_lun_parameter(
            cli, name=name, pool=pool, size=size, sp=sp, is_thin=is_thin,
            host_access=host_access, description=description,
            io_limit_policy=io_limit_policy, is_repl_dst=is_repl_dst,
            tiering_policy=tiering_policy, snap_schedule=snap_schedule)
        resp = cli.type_action(UnityStorageResource().resource_class,
                               'createLun', **req_body)
        resp.raise_if_err()
        sr = UnityStorageResource(_id=resp.resource_id, cli=cli)
        return sr.luns[0]

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

    @property
    def io_limit_rule(self):
        rule = None
        if self.io_limit_policy:
            policy = self.io_limit_policy
            if policy.io_limit_rule_settings:
                rules = policy.io_limit_rule_settings
            elif policy.io_limit_rules:
                rules = policy.io_limit_rules
            else:
                rules = None

            if rules:
                rule = rules[0]
        return rule

    @property
    def total_size_gb(self):
        return self.size_total / (1024 ** 3)

    @total_size_gb.setter
    def total_size_gb(self, value):
        self.expand(value * 1024 ** 3)

    @property
    def max_iops(self):
        return self.effective_io_limit_max_iops

    @property
    def max_kbps(self):
        return self.effective_io_limit_max_kbps

    def expand(self, new_size):
        """ expand the LUN to a new size

        :param new_size: new size in bytes.
        :return: the old size
        """
        ret = self.size_total
        resp = self.modify(size=new_size)
        resp.raise_if_err()
        return ret

    @staticmethod
    def _compose_lun_parameter(cli, **kwargs):
        sp = kwargs.get('sp')
        if isinstance(sp, UnityStorageProcessor):
            sp_node = sp.to_node_enum()
        else:
            sp_node = None

        TieringPolicyEnum.verify(kwargs.get('tiering_policy'))
        NodeEnum.verify(sp_node)

        # TODO: snap_schedule
        req_body = cli.make_body(
            name=kwargs.get('name'),
            description=kwargs.get('description'),
            replicationParameters=cli.make_body(
                isReplicationDestination=kwargs.get('is_repl_dst')
            ),
            lunParameters=cli.make_body(
                isThinEnabled=kwargs.get('is_thin'),
                size=kwargs.get('size'),
                pool=kwargs.get('pool'),
                defaultNode=sp_node,
                fastVPParameters=cli.make_body(
                    tieringPolicy=kwargs.get('tiering_policy')),
                ioLimitParameters=cli.make_body(
                    ioLimitPolicy=kwargs.get('io_limit_policy'))
            )
        )

        # Empty host access can be used to wipe the host_access
        host_access_value = cli.make_body(
            kwargs.get('host_access'), allow_empty=True)

        if host_access_value is not None:
            if 'lunParameters' not in req_body:
                req_body['lunParameters'] = {}
            req_body['lunParameters']['hostAccess'] = host_access_value

        return req_body

    def modify(self, name=None, size=None, host_access=None,
               description=None, is_thin=None, sp=None, io_limit_policy=None,
               is_repl_dst=None, tiering_policy=None, snap_schedule=None):

        req_body = self._compose_lun_parameter(
            self._cli, name=name, pool=None, size=size, sp=sp,
            host_access=host_access, is_thin=is_thin, description=description,
            io_limit_policy=io_limit_policy, is_repl_dst=is_repl_dst,
            tiering_policy=tiering_policy, snap_schedule=snap_schedule,
        )
        resp = self._cli.action(UnityStorageResource().resource_class,
                                self.get_id(), 'modifyLun', **req_body)
        resp.raise_if_err()
        return resp

    def delete(self, async=False, force_snap_delete=False,
               force_vvol_delete=False):
        sr = self.storage_resource
        if not self.existed or sr is None:
            raise UnityResourceNotFoundError(
                'cannot find lun {}.'.format(self.get_id()))
        resp = self._cli.delete(sr.resource_class, self.get_id(),
                                forceSnapDeletion=force_snap_delete,
                                forceVvolDeletion=force_vvol_delete,
                                async=async)
        resp.raise_if_err()
        return resp

    def attach_to(self, host, access_mask=HostLUNAccessEnum.PRODUCTION):
        host_access = [{'host': host, 'accessMask': access_mask}]
        # If this lun has been attached to other host, don't overwrite it.
        if self.host_access:
            host_access += [{'host': item.host,
                             'accessMask': item.access_mask} for item
                            in self.host_access if host.id != item.host.id]

        resp = self.modify(host_access=host_access)
        resp.raise_if_err()
        return resp

    def detach_from(self, host):
        if self.host_access is None or not host:
            return None

        new_access = [{'host': item.host,
                       'accessMask': item.access_mask} for item
                      in self.host_access if host.id != item.host.id]
        resp = self.modify(host_access=new_access)
        resp.raise_if_err()
        return resp

    def create_snap(self, name=None, description=None, is_auto_delete=None,
                    retention_duration=None):
        return UnitySnap.create(self._cli, self.storage_resource,
                                name=name, description=description,
                                is_auto_delete=is_auto_delete,
                                retention_duration=retention_duration,
                                is_read_only=None, fs_access_type=None)

    @property
    def snapshots(self):
        return UnitySnapList(cli=self._cli,
                             storage_resource=self.storage_resource)


class UnityLunList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityLun
