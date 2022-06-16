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

from storops.unity import resource
import storops.unity.resource.cifs_share
import storops.unity.resource.interface
import storops.unity.resource.nas_server

__author__ = 'Jay Xu'

LOG = logging.getLogger(__name__)


class UnityCifsServer(resource.UnityResource):
    @classmethod
    def create(cls, cli, nas_server, interfaces=None,
               netbios_name=None, name=None,
               domain=None, domain_username=None, domain_password=None,
               workgroup=None, local_password=None):
        if interfaces is None:
            interfaces = []
        nas_server_clz = storops.unity.resource.nas_server.UnityNasServer
        fi_clz = storops.unity.resource.interface.UnityFileInterface

        nas_server = nas_server_clz.get(cli, nas_server)
        interfaces = [fi_clz.get(cli, fi) for fi in interfaces]
        resp = cli.post(cls().resource_class,
                        nasServer=nas_server,
                        netbiosName=netbios_name,
                        name=name,
                        domain=domain,
                        domainUsername=domain_username,
                        domainPassword=domain_password,
                        interfaces=interfaces,
                        workgroup=workgroup,
                        localAdminPassword=local_password)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    @classmethod
    def get(cls, cli, _id=None):
        nas_server_clz = storops.unity.resource.nas_server.UnityNasServer
        if isinstance(_id, nas_server_clz):
            ret = _id.get_cifs_server()
        elif not isinstance(_id, cls):
            ret = cls(_id=_id, cli=cli)
        else:
            ret = _id
        return ret

    def create_cifs_share(self, name, fs, path=None):
        clz = storops.unity.resource.cifs_share.UnityCifsShare
        return clz.create(self._cli, name=name, fs=fs,
                          path=path, cifs_server=self)

    def delete(self, skip_domain_unjoin=None, username=None,
               password=None, async_mode=False):
        resp = self._cli.delete(self.resource_class,
                                self.get_id(),
                                skipUnjoin=skip_domain_unjoin,
                                domainUsername=username,
                                domainPassword=password,
                                async_mode=async_mode)
        resp.raise_if_err()
        return resp

    def modify(self, netbios_name=None, name=None,
               domain=None, domain_username=None, domain_password=None,
               workgroup=None, local_password=None):
        req_body = self._cli.make_body(netbiosName=netbios_name,
                                       name=name,
                                       domain=domain,
                                       domainUsername=domain_username,
                                       domainPassword=domain_password,
                                       workgroup=workgroup,
                                       localAdminPassword=local_password)

        resp = self.action('modify', **req_body)
        resp.raise_if_err()
        return resp


class UnityCifsServerList(resource.UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityCifsServer
