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

import storops.exception
from storops.lib.common import instance_cache
from storops.lib.resource import ResourceList
from storops.unity.calculator import calculators
from storops.unity.client import UnityClient
from storops.unity.enums import UnityEnum, DNSServerOriginEnum
from storops.unity.resource import UnityResource, UnityResourceList, \
    UnitySingletonResource
from storops.unity.resource.cifs_server import UnityCifsServerList
from storops.unity.resource.cifs_share import UnityCifsShareList
from storops.unity.resource.disk import UnityDiskList
from storops.unity.resource.dns_server import UnityFileDnsServerList
from storops.unity.resource.filesystem import UnityFileSystemList
from storops.unity.resource.host import UnityHost, UnityHostList, \
    UnityHostIpPortList, UnityHostInitiatorList
from storops.unity.resource.interface import UnityFileInterfaceList
from storops.unity.resource.lun import UnityLunList
from storops.unity.resource.metric import UnityMetricRealTimeQuery
from storops.unity.resource.nas_server import UnityNasServerList
from storops.unity.resource.nfs_server import UnityNfsServerList
from storops.unity.resource.nfs_share import UnityNfsShareList
from storops.unity.resource.pool import UnityPoolList
from storops.unity.resource.port import UnityIpPortList, UnityIoLimitPolicy, \
    UnityIoLimitPolicyList, UnityLinkAggregationList
from storops.unity.resource.snap import UnitySnapList
from storops.unity.resource.sp import UnityStorageProcessorList

from storops.unity.resource.tenant import UnityTenant, UnityTenantList
from storops.unity.resource.port import UnityEthernetPortList, \
    UnityIscsiPortalList, UnityFcPortList
from storops.unity.resource.storage_resource import UnityConsistencyGroup, \
    UnityConsistencyGroupList
from storops.unity.resource.vmware import UnityCapabilityProfileList
from storops.lib.version import version

__author__ = 'Jay Xu, Cedric Zhuang'

LOG = logging.getLogger(__name__)


class UnitySystem(UnitySingletonResource):
    def __init__(self, host=None, username=None, password=None,
                 port=443, cli=None, verify=False):
        super(UnitySystem, self).__init__(cli=cli)
        if cli is None:
            self._cli = UnityClient(host, username, password, port,
                                    verify=verify)
        else:
            self._cli = cli

    def get_capability_profile(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityCapabilityProfileList,
                                   _id=_id, name=name, **filters)

    def get_sp(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityStorageProcessorList, _id=_id,
                                   name=name, **filters)

    def get_iscsi_portal(self, _id=None, **filters):
        return self._get_unity_rsc(UnityIscsiPortalList, _id=_id, **filters)

    def get_fc_port(self, _id=None, **filters):
        return self._get_unity_rsc(UnityFcPortList, _id=_id, **filters)

    def get_ethernet_port(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityEthernetPortList, _id=_id,
                                   name=name, **filters)

    def create_host(self, name, host_type=None, desc=None, os=None,
                    tenant=None):
        host = UnityHostList.get(self._cli, name=name)
        if host:
            raise storops.exception.UnityHostNameInUseError()
        else:
            host = UnityHost.create(self._cli, name, host_type=host_type,
                                    desc=desc, os=os, tenant=tenant)

        return host

    def get_initiator(self, _id=None, **filters):
        return self._get_unity_rsc(UnityHostInitiatorList, _id=_id, **filters)

    def get_lun(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityLunList, _id=_id, name=name, **filters)

    def get_pool(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityPoolList, _id=_id, name=name,
                                   **filters)

    def get_nas_server(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityNasServerList, _id=_id, name=name,
                                   **filters)

    def get_cifs_server(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityCifsServerList, _id=_id, name=name,
                                   **filters)

    def get_nfs_server(self, _id=None, **filters):
        return self._get_unity_rsc(UnityNfsServerList, _id=_id, **filters)

    def get_snap(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnitySnapList, _id=_id, name=name,
                                   **filters)

    def create_nas_server(self, name, sp=None, pool=None, is_repl_dst=None,
                          multi_proto=None, tenant=None):
        if sp is None:
            sp = self._auto_balance_sp()

        return sp.create_nas_server(name, pool,
                                    is_repl_dst=is_repl_dst,
                                    multi_proto=multi_proto, tenant=tenant)

    def _auto_balance_sp(self):
        sp_list = self.get_sp()
        if len(sp_list) < 2:
            LOG.debug('spb not present. pick spa to host nas server.')
            return sp_list.first_item

        servers = self.get_nas_server()
        spa, spb = sp_list
        servers_on_spa = servers.shadow_copy(home_sp=spa)
        sp = spb if len(servers_on_spa) * 2 > len(servers) else spa
        LOG.debug('pick %s to balance of spa and spb to host nas servers.',
                  sp.get_id())
        return sp

    def get_ip_port(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityIpPortList, _id=_id, name=name,
                                   **filters)

    def get_file_interface(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityFileInterfaceList, _id=_id, name=name,
                                   **filters)

    def get_dns_server(self, _id=None, **filters):
        return self._get_unity_rsc(UnityFileDnsServerList, _id=_id, **filters)

    def get_filesystem(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityFileSystemList, _id=_id, name=name,
                                   **filters)

    def get_cifs_share(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityCifsShareList, _id=_id, name=name,
                                   **filters)

    def get_nfs_share(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityNfsShareList, _id=_id, name=name,
                                   **filters)

    def get_host(self, _id=None, name=None, address=None, **filters):
        ret = UnityHostList.get(self._cli, name='not found')
        if address:
            host_ip_ports = UnityHostIpPortList.get(self._cli, address=address)
            if host_ip_ports:
                ret = host_ip_ports[0].host
        else:
            ret = self._get_unity_rsc(UnityHostList, _id=_id, name=name,
                                      **filters)
        return ret

    def get_io_limit_policy(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityIoLimitPolicyList, _id=_id, name=name,
                                   **filters)

    def create_io_limit_policy(self, name, max_iops=None, max_kbps=None,
                               policy_type=None, is_shared=None,
                               description=None):
        return UnityIoLimitPolicy.create(
            self._cli, name, max_iops=max_iops, max_kbps=max_kbps,
            policy_type=policy_type, is_shared=is_shared,
            description=description)

    def get_cg(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityConsistencyGroupList, _id=_id,
                                   name=name, **filters)

    def create_cg(self, name, description=None, lun_list=None, hosts=None):
        return UnityConsistencyGroup.create(
            self._cli, name, description=description, lun_list=lun_list,
            hosts=hosts)

    def get_doc(self, resource):
        if isinstance(resource, (UnityResource, UnityEnum)):
            clz = resource.__class__
        else:
            clz = resource
        return self._cli.get_doc(clz)

    @version('>=4.1')
    def create_tenant(self, name, uuid=None, vlans=None):
        return UnityTenant.create(self._cli, name, uuid=uuid, vlans=vlans)

    @version('>=4.1')
    def get_tenant(self, _id=None, **filters):
        return self._get_unity_rsc(UnityTenantList, _id=_id, **filters)

    @version('>=4.1')
    def get_tenant_use_vlan(self, vlan):
        tenant = self.get_tenant(vlans=[vlan])
        if len(tenant) == 0:
            return None
        else:
            return tenant[0]

    @property
    @instance_cache
    def _system_time(self):
        return UnitySystemTime(self._cli)

    @property
    def system_time(self):
        return self._system_time.time

    def set_system_time(self, new_time=None):
        return self._system_time.set(new_time)

    @property
    @instance_cache
    def _ntp_server(self):
        return UnityNtpServer(self._cli)

    @property
    def ntp_server(self):
        return self._ntp_server.addresses

    def add_ntp_server(self, *addresses):
        return self._ntp_server.add(*addresses)

    def remove_ntp_server(self, *addresses):
        return self._ntp_server.remove(*addresses)

    def clear_ntp_server(self):
        return self._ntp_server.clear()

    @property
    @instance_cache
    def dns_server(self):
        return UnityDnsServer(self._cli)

    def add_dns_server(self, *addresses):
        return self.dns_server.add(*addresses)

    def remove_dns_server(self, *addresses):
        return self.dns_server.remove(*addresses)

    def clear_dns_server(self, use_dhcp=None):
        """ Clear the DNS server settings.

        :param use_dhcp: default to True, clear all settings and fallback to
                         use DHCP settings.
        :return: last settings
        """
        return self.dns_server.clear(use_dhcp)

    def get_disk(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityDiskList, _id=_id, name=name,
                                   **filters)

    @property
    @instance_cache
    def info(self):
        return UnityBasicSystemInfo.get(cli=self._cli)

    def get_link_aggregation(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityLinkAggregationList, _id=_id,
                                   name=name,
                                   **filters)

    def enable_perf_stats(self, interval=None, rsc_clz_list=None):
        if interval is None:
            interval = 60
        if rsc_clz_list is None:
            rsc_list_collection = self._default_rsc_list_with_perf_stats()
            rsc_clz_list = ResourceList.get_rsc_clz_list(rsc_list_collection)

        def get_real_time_query_list():
            paths = calculators.get_all_paths(rsc_clz_list)
            return UnityMetricRealTimeQuery.get_query_list(
                self._cli, interval, paths=paths)

        def f():
            query_list = get_real_time_query_list()
            if query_list:
                paths = calculators.get_all_paths(rsc_clz_list)
                ret = query_list.get_query_result(paths)
            else:
                ret = None
            return ret

        queries = get_real_time_query_list()
        self._cli.enable_perf_metric(interval, f, rsc_clz_list)
        return queries

    def disable_perf_stats(self):
        self._cli.disable_perf_metric()

    def is_perf_stats_enabled(self):
        return self._cli.is_perf_metric_enabled()

    def get_metric_query_result(self, query_id):
        return UnityMetricRealTimeQuery(
            cli=self._cli, _id=query_id).get_query_result()

    def add_metric_record(self, record):
        self._cli.add_metric_record(record)

    def enable_persist_perf_stats(self):
        rsc_list = self._default_rsc_list_with_perf_stats()
        self._cli.persist_perf_stats(rsc_list)

    def disable_persist_perf_stats(self):
        self._cli.persist_perf_stats(None)

    def _default_rsc_list_with_perf_stats(self):
        return (self.get_sp(),
                self.get_lun(),
                self.get_filesystem(),
                self.get_disk(inserted=True))

    def is_perf_stats_persisted(self):
        return self._cli.is_perf_stats_persisted()


class UnitySystemList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySystem


class UnityDpe(UnityResource):
    pass


class UnityDpeList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityDpe


class UnityVirusChecker(UnityResource):
    pass


class UnityVirusCheckerList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityVirusChecker


class UnityBasicSystemInfo(UnitySingletonResource):
    pass


class UnityBasicSystemInfoList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityBasicSystemInfo


class UnitySystemTime(UnitySingletonResource):
    def set(self, new_time, reboot=None):
        old_time = self.time

        if reboot:
            reboot = 1
        else:
            reboot = 0

        time_str = new_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        resp = self.modify(time=time_str, rebootPrivilege=reboot)
        resp.raise_if_err()
        self.update()
        return old_time


class _UnityNtpDnsServerCommonBase(UnitySingletonResource):
    def _do_modify(self, *addresses):
        raise NotImplementedError('Should be implemented by child classes.')

    def set(self, *addresses):
        exists = self.addresses
        resp = self._do_modify(*addresses)
        resp.raise_if_err()
        self.update()
        return exists

    def add(self, *addresses):
        new_addresses = set(self.addresses).union(set(addresses))
        return self.set(*new_addresses)

    def remove(self, *addresses):
        new_addresses = set(self.addresses) - set(addresses)
        return self.set(*new_addresses)

    def clear(self):
        return self.set()


class UnityNtpServer(_UnityNtpDnsServerCommonBase):
    def _do_modify(self, *addresses):
        return self.modify(addresses=sorted(addresses), rebootPrivilege=0)


class UnityDnsServer(_UnityNtpDnsServerCommonBase):
    def _do_modify(self, *addresses):
        return self.modify(addresses=sorted(addresses))

    def clear(self, use_dhcp=None):
        if use_dhcp is None:
            use_dhcp = True

        if use_dhcp:
            origin = DNSServerOriginEnum.DHCP
        else:
            origin = None

        exists = self.addresses
        resp = self.modify(addresses=[], origin=origin)
        resp.raise_if_err()
        self.update()
        return exists
