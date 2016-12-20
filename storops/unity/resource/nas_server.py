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

import storops.unity.resource.interface
import storops.unity.resource.cifs_server
import storops.unity.resource.nfs_server
import storops.unity.resource.dns_server
import storops.unity.resource.pool
from storops.exception import UnityCifsServiceNotEnabledError
from storops.unity.resource import UnityResource, UnityResourceList
from storops.unity.resource.sp import UnityStorageProcessor
from storops.unity.resource.tenant import UnityTenant

__author__ = 'Jay Xu'

log = logging.getLogger(__name__)


class UnityNasServer(UnityResource):
    @classmethod
    def create(cls, cli, name, sp, pool, is_repl_dst=None,
               multi_proto=None,
               tenant=None):
        sp = UnityStorageProcessor.get(cli, sp)
        pool_clz = storops.unity.resource.pool.UnityPool
        pool = pool_clz.get(cli, pool)
        if tenant is not None:
            tenant = UnityTenant.get(cli, tenant)

        resp = cli.post(cls().resource_class,
                        name=name,
                        homeSP=sp,
                        pool=pool,
                        isReplicationDestination=is_repl_dst,
                        isMultiProtocolEnabled=multi_proto,
                        tenant=tenant)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def delete(self, skip_domain_unjoin=None, username=None,
               password=None, async=False):
        resp = self._cli.delete(self.resource_class,
                                self.get_id(),
                                skipDomainUnjoin=skip_domain_unjoin,
                                domainUsername=username,
                                domainPassword=password,
                                async=async)
        resp.raise_if_err()
        return resp

    def create_file_interface(self, ip_port, ip,
                              netmask=None, gateway=None,
                              vlan_id=None, role=None):
        clz = storops.unity.resource.interface.UnityFileInterface
        return clz.create(self._cli, self,
                          ip_port=ip_port, ip=ip,
                          netmask=netmask, gateway=gateway,
                          vlan_id=vlan_id, role=role)

    def create_cifs_server(self, interfaces=None,
                           netbios_name=None, name=None,
                           domain=None, domain_username=None,
                           domain_password=None,
                           workgroup=None, local_password=None):
        clz = storops.unity.resource.cifs_server.UnityCifsServer
        return clz.create(self._cli, self,
                          interfaces=interfaces,
                          netbios_name=netbios_name,
                          name=name,
                          domain=domain,
                          domain_username=domain_username,
                          domain_password=domain_password,
                          workgroup=workgroup,
                          local_password=local_password)

    def enable_cifs_service(self, interfaces=None,
                            netbios_name=None, name=None,
                            domain=None, domain_username=None,
                            domain_password=None,
                            workgroup=None, local_password=None
                            ):
        if domain_username is not None and domain is None:
            dns_server = self.file_dns_server
            if dns_server is not None:
                domain = dns_server.domain
        self.create_cifs_server(interfaces=interfaces,
                                netbios_name=netbios_name,
                                name=name,
                                domain=domain,
                                domain_username=domain_username,
                                domain_password=domain_password,
                                workgroup=workgroup,
                                local_password=local_password)

    def create_nfs_server(self, host_name=None, nfs_v4_enabled=True,
                          kdc_type=None, kdc_username=None, kdc_password=None):
        clz = storops.unity.resource.nfs_server.UnityNfsServer
        return clz.create(self._cli, self,
                          host_name=host_name,
                          nfs_v4_enabled=nfs_v4_enabled,
                          kdc_type=kdc_type,
                          kdc_username=kdc_username,
                          kdc_password=kdc_password)

    def enable_nfs_service(self, host_name=None, nfs_v4_enabled=True,
                           kdc_type=None, kdc_username=None,
                           kdc_password=None):
        self.create_nfs_server(host_name=host_name,
                               nfs_v4_enabled=nfs_v4_enabled,
                               kdc_type=kdc_type,
                               kdc_username=kdc_username,
                               kdc_password=kdc_password)

    def create_dns_server(self, domain, *ip_list):
        clz = storops.unity.resource.dns_server.UnityFileDnsServer
        return clz.create(self._cli, self, domain=domain, ip_list=ip_list)

    def get_cifs_server(self):
        cifs_server_list = self.cifs_server
        if cifs_server_list:
            ret = cifs_server_list[0]
        else:
            raise UnityCifsServiceNotEnabledError(
                'CIFS is not enabled on {}.'.format(self.name))
        return ret


class UnityNasServerList(UnityResourceList):
    def __init__(self, cli=None, home_sp=None, current_sp=None, **filters):
        super(UnityNasServerList, self).__init__(cli, **filters)
        self._home_sp_id = None
        self._current_sp_id = None
        self._set_filter(home_sp, current_sp)

    def _set_filter(self, home_sp=None, current_sp=None, **kwargs):
        self._home_sp_id, self._current_sp_id = (
            [sp.get_id() if isinstance(sp, UnityStorageProcessor)
             else sp for sp in (home_sp, current_sp)])

    def _filter(self, nas_server):
        ret = True
        if self._home_sp_id is not None:
            ret &= nas_server.home_sp.get_id() == self._home_sp_id
        if self._current_sp_id is not None:
            ret &= nas_server.current_sp.get_id() == self._current_sp_id
        return ret

    @classmethod
    def get_resource_class(cls):
        return UnityNasServer
