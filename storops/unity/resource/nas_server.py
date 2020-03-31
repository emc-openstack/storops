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

import storops.unity.resource.cifs_server
import storops.unity.resource.dns_server
import storops.unity.resource.interface
import storops.unity.resource.nfs_server
import storops.unity.resource.pool
from storops.exception import UnityCifsServiceNotEnabledError, \
    UnityPolicyInvalidParametersError
from storops.unity.enums import ReplicationEndpointResourceTypeEnum
from storops.unity.resource import UnityResource, UnityResourceList
from storops.unity.resource.replication_session import UnityResourceConfig, \
    UnityReplicationSession
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
               password=None, async_mode=False):
        resp = self._cli.delete(self.resource_class,
                                self.get_id(),
                                skipDomainUnjoin=skip_domain_unjoin,
                                domainUsername=username,
                                domainPassword=password,
                                async_mode=async_mode)
        resp.raise_if_err()
        return resp

    def create_file_interface(self, ip_port, ip, netmask=None, gateway=None,
                              vlan_id=None, role=None,
                              v6_prefix_length=None):
        clz = storops.unity.resource.interface.UnityFileInterface
        return clz.create(self._cli, self,
                          ip_port=ip_port, ip=ip, netmask=netmask,
                          gateway=gateway, vlan_id=vlan_id, role=role,
                          v6_prefix_length=v6_prefix_length)

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

    def replicate(self, dst_nas_server_id, max_time_out_of_sync,
                  remote_system=None, replication_name=None):
        """
        Creates a replication session with an existing nas server as
        destination.

        :param dst_nas_server_id: destination nas server id.
        :param max_time_out_of_sync: maximum time to wait before syncing the
            source and destination. Value `-1` means the automatic sync is not
            performed. `0` means it is a sync replication.
        :param remote_system: `UnityRemoteSystem` object. The remote system to
            which the replication is being configured. When not specified, it
            defaults to local system.
        :param replication_name: replication name.
        :return: created replication session.
        """

        return UnityReplicationSession.create(
            self._cli, self.get_id(), dst_nas_server_id, max_time_out_of_sync,
            name=replication_name, remote_system=remote_system)

    def replicate_with_dst_resource_provisioning(self, max_time_out_of_sync,
                                                 dst_pool_id,
                                                 dst_nas_server_name=None,
                                                 remote_system=None,
                                                 replication_name=None,
                                                 dst_sp=None,
                                                 is_backup_only=None):
        """
        Creates a replication session with destination nas server provisioning.

        :param max_time_out_of_sync: maximum time to wait before syncing the
            source and destination. Value `-1` means the automatic sync is not
            performed. `0` means it is a sync replication.
        :param dst_pool_id: id of pool to allocate destination nas server.
        :param dst_nas_server_name: destination nas server name.
        :param remote_system: `UnityRemoteSystem` object. The remote system to
            which the replication is being configured. When not specified, it
            defaults to local system.
        :param replication_name: replication name.
        :param dst_sp: `NodeEnum` value. Default storage processor of
            destination nas server. It is required to create remote
            replication.
        :param is_backup_only: is backup only or not.
        :return: created replication session.
        """
        if remote_system and (dst_sp is None):
            message = 'Default storage processor is required to create ' \
                      'replication session with remote Unity system.'
            raise UnityPolicyInvalidParametersError(message)
        dst_resource = UnityResourceConfig.to_embedded(
            name=dst_nas_server_name, pool_id=dst_pool_id,
            default_sp=dst_sp, is_backup_only=is_backup_only,
            replication_resource_type=(
                ReplicationEndpointResourceTypeEnum.NASSERVER))
        return UnityReplicationSession.create_with_dst_resource_provisioning(
            self._cli, self.get_id(), dst_resource, max_time_out_of_sync,
            remote_system=remote_system, name=replication_name,
        )

    def modify(self, name=None, sp=None, is_replication_destination=None,
               is_backup_only=None, current_unix_directory_service=None,
               is_multi_protocol_enabled=None, allow_unmapped_user=None,
               default_unix_user=None, default_windows_user=None,
               enable_windows_to_unix_username=None,
               is_packet_reflect_enabled=None, is_ignore_warnings=None):
        """
        Modify a NAS server.

        :param name: specify a new NAS server name.
        :param sp: specify the SP on which the VDM is to run.
        :param is_replication_destination: specify whether the NAS server
            is a replication destination. Values are:
            true - Replication destination NAS server.
            false - Normal NAS server.
        :param is_backup_only: specify whether the NAS server is used as
            backup only. Values are:
            true - NAS server acts as backup only.
            false - Normal NAS server.
        :param current_unix_directory_service: directory Service used for
            quering identity information for UNIX (such as UIDs, GIDs, net
            groups).
        :param is_multi_protocol_enabled: indicates whether multiprotocol
            sharing mode is enabled. Values are:
            true - Enable multiprotocol sharing.
            false - Disable multiprotocol sharing.
        :param allow_unmapped_user: use this flag to mandatory disable access
            in case of any user mapping failure. Values are:
            true - Enable access in case of any user mapping failure.
            false - Disable access in case of any user mapping failure.
        :param default_unix_user: default Unix user name used for granting
            access in case of Windows to Unix user mapping failure.
            When empty, access in such case is denied.
        :param default_windows_user: default Windows user name used for
            granting access in case of Unix to Windows user mapping failure.
            When empty, access in such case is denied.
        :param enable_windows_to_unix_username: indicates whether a
            Unix to/from Windows user name mapping is enabled. Values are:
            true - Unix to/from Windows user name mapping is enabled.
            false - Unix to/from Windows user name mapping is disabled.
        :param is_packet_reflect_enabled.
        :param is_ignore_warnings: is backup only or not.
        """
        req_body = self._cli.make_body(
            name=name, homeSP=sp,
            isReplicationDestination=is_replication_destination,
            isBackupOnly=is_backup_only,
            currentUnixDirectoryService=current_unix_directory_service,
            isMultiProtocolEnabled=is_multi_protocol_enabled,
            allowUnmappedUser=allow_unmapped_user,
            defaultUnixUser=default_unix_user,
            defaultWindowsUser=default_windows_user,
            enableWindowsToUnixUsernameMapping=enable_windows_to_unix_username,
            isPacketReflectEnabled=is_packet_reflect_enabled,
            isIgnoreWarnings=is_ignore_warnings)

        resp = self.action('modify', **req_body)
        resp.raise_if_err()
        return resp


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
