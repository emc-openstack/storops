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

__author__ = 'Jay Xu'

log = logging.getLogger(__name__)


class UnityLun(UnityResource):
    @classmethod
    def create(cls, cli, name, pool, size, sp=None, host_access=None,
               is_thin=None, description=None, iolimit_policy=None,
               is_repl_dst=None, tiering_policy=None, snap_schedule=None):

        pool_clz = storops.unity.resource.pool.UnityPool
        pool = pool_clz.get(cli, pool)
        TieringPolicyEnum.verify(tiering_policy)

        if sp is None:
            spNode = NodeEnum.SPA
        else:
            spNode = sp.to_node_enum()
            NodeEnum.verify(spNode)

        if tiering_policy is None:
            tiering_policy = TieringPolicyEnum.AUTOTIER

        if description is None:
            description = "Please specify Lun description"

        # TODO:iolimit_policy adn snap_schedule
        req_body = {
            'name': name,
            'description': description,
            'replicationParameters': {
                'isReplicationDestination': is_repl_dst
            },
            'lunParameters': {
                'pool': pool,
                'isThinEnabled': is_thin,
                'size': size,
                'fastVPParameters': {
                    'tieringPolicy': tiering_policy
                },
                'defaultNode': spNode,
            }
        }

        # compose host access parameters
        if host_access is not None:
            req_body['lunParameters']['hostAccess'] = []
            for ha in host_access:
                HostLUNAccessEnum.verify(ha['accessMask'])
                req_body['lunParameters']['hostAccess'].append(
                    {
                        'host': ha['host'],
                        'accessMask': ha['accessMask']
                    }
                )
        # end if

        resp = cli.type_action(UnityStorageResource().resource_class,
                               'createLun',
                               **req_body)
        resp.raise_if_err()
        sr = UnityStorageResource(_id=resp.resource_id, cli=cli)
        return sr.luns[0]

    def modify(self, name=None, size=None, host_access=None,
               description=None, is_thin=None, sp=None, iolimit_policy=None,
               is_repl_dst=None, tiering_policy=None, snap_schedule=None):

        if sp is not None:
            spNode = sp.to_node_enum()
            NodeEnum.verify(spNode)

        req_body = {}
        if name is not None:
            req_body['name'] = name
        if description is not None:
            req_body['description'] = description
        if is_repl_dst is not None:
            req_body['replicationParameters'] = {
                    'isReplicationDestination': is_repl_dst
            }

        # TODO:iolimit_policy and snap_schedule
        # Compose lun parameters
        req_body['lunParameters'] = {}
        if is_thin is not None:
            req_body['lunParameters']['isThinEnabled'] = is_thin
        if size is not None:
            req_body['lunParameters']['size'] = size
        if sp is not None:
            req_body['lunParameters']['defaultNode'] = spNode
        if tiering_policy is not None:
            req_body['lunParameters']['fastVPParameters'] = {
                    'tieringPolicy': tiering_policy
                }

        # compose host access parameters
        if host_access is not None:
            req_body['lunParameters']['hostAccess'] = []
            for ha in host_access:
                HostLUNAccessEnum.verify(ha['accessMask'])
                req_body['lunParameters']['hostAccess'].append(
                    {
                        'host': ha['host'],
                        'accessMask': ha['accessMask']
                    }
                )
        # end if

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

    def attach_to(self, host, max_retires=3,
                  access_mask=HostLUNAccessEnum.PRODUCTION):
        # TODO: max_retires to retry
        host_access = [{'host': host, 'accessMask': access_mask}]
        # If this lun has been attached to other host, don't overwrite it.
        if self.host_access:
            host_access += [{'host': item.host,
                            'accessMask': item.access_mask} for item
                            in self.host_access if host.id != item.host.id]

        resp = self.modify(host_access=host_access)
        return resp

    def detach_from(self, host, max_retires=3):
        # TODO: max_retires to retry
        if self.host_access is None or not host:
            return None

        new_access = [{
            'host': item.host,
            'accessMask': item.access_mask} for item
                in self.host_access if host.id != item.host.id]
        resp = self.modify(host_access=new_access)
        return resp


class UnityLunList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityLun
