# Copyright (c) 2016 EMC Corporation.
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
from storops.lib.version import version
import storops.unity.resource.nas_server

__author__ = 'Tina Tang'

LOG = logging.getLogger(__name__)


@version('>=4.1')
class UnityTenant(UnityResource):
    @classmethod
    def create(cls, cli, name, uuid=None, vlans=None):
        resp = cli.post(cls().resource_class,
                        name=name,
                        uuid=uuid,
                        vlans=vlans)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def modify(self, name=None, vlans=None):
        req_body = {}
        if name is not None:
            req_body['name'] = name
        if vlans is not None:
            req_body['vlans'] = vlans
        resp = self._cli.modify(self.resource_class,
                                self.get_id(), **req_body)
        resp.raise_if_err()
        return resp

    def delete(self, delete_hosts=False):
        if delete_hosts and self.hosts:
            for host in self.hosts:
                host.delete()
        return super(UnityTenant, self).delete()

    @property
    def nas_servers(self):
        clz = storops.unity.resource.nas_server.UnityNasServerList
        return clz(cli=self._cli, tenant=self)


@version('>=4.1')
class UnityTenantList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityTenant
