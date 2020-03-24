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
from storops.lib import job_helper
from storops.lib.common import instance_cache
from storops.lib.resource import ResourceList
from storops.lib.version import version
from storops.unity.calculator import calculators
from storops.unity.client import UnityClient
from storops.unity.enums import UnityEnum, DNSServerOriginEnum
from storops.unity.resource import UnityResource, UnityResourceList, \
    UnitySingletonResource, UnityAttributeResource
from storops.unity.resource.alert import UnityAlertList
from storops.unity.resource.alert_config_snmp import \
    UnityAlertConfigSNMPTarget, UnityAlertConfigSNMPTargetList
from storops.unity.resource.cifs_server import UnityCifsServerList
from storops.unity.resource.cifs_share import UnityCifsShareList
from storops.unity.resource.disk import UnityDiskList, UnityDiskGroupList
from storops.unity.resource.dns_server import UnityFileDnsServerList
from storops.unity.resource.filesystem import UnityFileSystemList
from storops.unity.resource.host import UnityHost, UnityHostList, \
    UnityHostIpPortList, UnityHostInitiatorList
from storops.unity.resource.import_session import UnityImportSessionList
from storops.unity.resource.interface import UnityFileInterfaceList
from storops.unity.resource.job import UnityJobList
from storops.unity.resource.lun import UnityLunList
from storops.unity.resource.metric import UnityMetricRealTimeQuery
from storops.unity.resource.move_session import UnityMoveSessionList
from storops.unity.resource.nas_server import UnityNasServerList
from storops.unity.resource.nfs_server import UnityNfsServerList
from storops.unity.resource.nfs_share import UnityNfsShareList
from storops.unity.resource.pool import UnityPoolList, UnityPool
from storops.unity.resource.port import UnityEthernetPortList, \
    UnityIscsiPortalList, UnityFcPortList, UnityIoModuleList
from storops.unity.resource.port import UnityIpPortList, UnityIoLimitPolicy, \
    UnityIoLimitPolicyList, UnityLinkAggregationList, UnityIscsiPortal, \
    UnitySasPortList, UnityIscsiNodeList
from storops.unity.resource.remote_interface import UnityRemoteInterfaceList
from storops.unity.resource.remote_system import UnityRemoteSystemList, \
    UnityRemoteSystem
from storops.unity.resource.replication_interface import \
    UnityReplicationInterfaceList, UnityReplicationInterface
from storops.unity.resource.replication_session import \
    UnityReplicationSessionList
from storops.unity.resource.snap import UnitySnapList
from storops.unity.resource.snap_schedule import UnitySnapScheduleList, \
    UnitySnapSchedule
from storops.unity.resource.sp import UnityStorageProcessorList
from storops.unity.resource.cg import UnityConsistencyGroup, \
    UnityConsistencyGroupList
from storops.unity.resource.tenant import UnityTenant, UnityTenantList
from storops.unity.resource.vmware import UnityCapabilityProfileList

__author__ = 'Jay Xu, Cedric Zhuang'

LOG = logging.getLogger(__name__)


class UnitySystem(UnitySingletonResource):
    def __init__(self, host=None, username=None, password=None,
                 port=443, cli=None, verify=False, retries=None,
                 cache_interval=0):
        super(UnitySystem, self).__init__(cli=cli)
        if cli is None:
            self._cli = UnityClient(host, username, password, port,
                                    verify=verify, retries=retries,
                                    cache_interval=cache_interval)
        else:
            self._cli = cli

        # Start job helper to handle async operations.
        job_helper.get_job_helper(self._cli)

    @classmethod
    def get_resource_class(cls):
        return cls

    def get_capability_profile(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityCapabilityProfileList,
                                   _id=_id, name=name, **filters)

    def get_sp(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityStorageProcessorList, _id=_id,
                                   name=name, **filters)

    def get_iscsi_portal(self, _id=None, **filters):
        return self._get_unity_rsc(UnityIscsiPortalList, _id=_id, **filters)

    def get_iscsi_node(self, _id=None, **filters):
        return self._get_unity_rsc(UnityIscsiNodeList, _id=_id, **filters)

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

    def create_pool(self, name, raid_groups, description=None, **kwargs):
        """Create pool based on RaidGroupParameter.

        :param name: pool name
        :param raid_groups: a list of *RaidGroupParameter*
        :param description: pool description
        :param alert_threshold: Threshold at which the system will generate
               alerts about the free space in the pool, specified as
               a percentage.
        :param is_harvest_enabled:
               True - Enable pool harvesting for the pool.
               False - Disable pool harvesting for the pool.
        :param is_snap_harvest_enabled:
               True - Enable snapshot harvesting for the pool.
               False - Disable snapshot harvesting for the pool.
        :param pool_harvest_high_threshold: Pool used space high threshold at
               which the system will automatically starts to delete snapshots
               in the pool
        :param pool_harvest_low_threshold: Pool used space low threshold under
               which the system will automatically stop deletion of snapshots
               in the pool
        :param snap_harvest_high_threshold: Snapshot used space high threshold
               at which the system automatically starts to delete snapshots
               in the pool
        :param snap_harvest_low_threshold: Snapshot used space low threshold
               below which the system will stop automatically deleting
               snapshots in the pool
        :param is_fast_cache_enabled:
               True - FAST Cache will be enabled for this pool.
               False - FAST Cache will be disabled for this pool.
        :param is_fastvp_enabled:
               True - Enable scheduled data relocations for the pool.
               False - Disable scheduled data relocations for the pool.
        :param pool_type:
               StoragePoolTypeEnum.TRADITIONAL - Create traditional pool.
               StoragePoolTypeEnum.DYNAMIC - Create dynamic pool. (default)
        """
        return UnityPool.create(self._cli, name=name, description=description,
                                raid_groups=raid_groups, **kwargs)

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

    @version(">=4.1")
    def get_file_port(self):
        """Returns ports list can be used by File

        File ports includes ethernet ports and link aggregation ports.
        """
        eths = self.get_ethernet_port(bond=False)
        las = self.get_link_aggregation()
        return eths + las

    @version("<4.1")  # noqa
    def get_file_port(self):
        """Returns ports list can be used by File

        File ports includes ethernet ports and link aggregation ports.
        """
        eths = self.get_ethernet_port()
        return eths.list

    def get_file_interface(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityFileInterfaceList, _id=_id, name=name,
                                   **filters)

    def create_iscsi_portal(self, ethernet_port, ip, netmask=None,
                            v6_prefix_len=None, vlan=None, gateway=None):
        return UnityIscsiPortal.create(
            cli=self._cli, ethernet_port=ethernet_port, ip=ip, netmask=netmask,
            v6_prefix_len=v6_prefix_len, vlan=vlan, gateway=gateway)

    def get_dns_server(self, _id=None, **filters):
        return self._get_unity_rsc(UnityFileDnsServerList, _id=_id, **filters)

    def get_filesystem(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityFileSystemList, _id=_id, name=name,
                                   **filters)

    def get_cifs_share(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityCifsShareList, _id=_id, name=name,
                                   allow_dup=True, **filters)

    def get_nfs_share(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityNfsShareList, _id=_id, name=name,
                                   allow_dup=True, **filters)

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
                               description=None, max_iops_density=None,
                               max_kbps_density=None, burst_rate=None,
                               burst_time=None, burst_frequency=None):
        return UnityIoLimitPolicy.create(
            self._cli, name, max_iops=max_iops, max_kbps=max_kbps,
            policy_type=policy_type, is_shared=is_shared,
            description=description,
            max_iops_density=max_iops_density,
            max_kbps_density=max_kbps_density,
            burst_rate=burst_rate,
            burst_time=burst_time,
            burst_frequency=burst_frequency)

    def get_cg(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(UnityConsistencyGroupList, _id=_id,
                                   name=name, **filters)

    def create_cg(self, name, description=None, lun_add=None, hosts=None):
        return UnityConsistencyGroup.create(
            self._cli, name, description=description, lun_add=lun_add,
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

    def get_disk_group(self, _id=None):
        return self._get_unity_rsc(UnityDiskGroupList, _id=_id)

    def get_dae(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityDaeList, _id=_id, name=name, **filters)

    def get_dpe(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityDpeList, _id=_id, name=name, **filters)

    def get_sas_port(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnitySasPortList, _id=_id, name=name, **filters)

    def get_io_module(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityIoModuleList, _id=_id, name=name, **filters)

    def get_lcc(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityLccList, _id=_id, name=name, **filters)

    def get_memory_module(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityMemoryModuleList, _id=_id, name=name, **filters)

    def get_fan(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityFanList, _id=_id, name=name, **filters)

    def get_power_supply(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityPowerSupplyList, _id=_id, name=name, **filters)

    def get_battery(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityBatteryList, _id=_id, name=name, **filters)

    def get_ssc(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnitySscList, _id=_id, name=name, **filters)

    def get_ssd(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnitySsdList, _id=_id, name=name, **filters)

    def get_license(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityLicenseList, _id=_id, name=name, **filters)

    def get_feature(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityFeatureList, _id=_id, name=name, **filters)

    def get_mgmt_interface(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityMgmtInterfaceList, _id=_id, **filters)

    def get_system_capacity(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnitySystemCapacityList, _id=_id, **filters)

    def get_move_session(self, _id=None, **filters):
        return self._get_unity_rsc(UnityMoveSessionList, _id=_id, **filters)

    @property
    @instance_cache
    def info(self):
        return UnityBasicSystemInfo.get(cli=self._cli)

    @version('>=4.1')
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
                self.get_disk(inserted=True),
                self.get_fc_port(),
                self.get_iscsi_node(),
                self.update(),
                )

    def is_perf_stats_persisted(self):
        return self._cli.is_perf_stats_persisted()

    def upload_license(self, license):
        files = {'filename': license}
        resp = self._cli.rest_post('/upload/license', files=files)
        resp.raise_if_err()

    def get_remote_system(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityRemoteSystemList, _id=_id, name=name, **filters)

    def create_remote_system(self, management_address,
                             local_username=None, local_password=None,
                             remote_username=None, remote_password=None,
                             connection_type=None):
        """
        Configures a remote system for remote replication.

        :param management_address: the management IP address of the remote
            system.
        :param local_username: administrative username of local system.
        :param local_password: administrative password of local system.
        :param remote_username: administrative username of remote system.
        :param remote_password: administrative password of remote system.
        :param connection_type: `ReplicationCapabilityEnum`. Replication
            connection type to the remote system.
        :return: the newly created remote system.
        """
        return UnityRemoteSystem.create(self._cli, management_address,
                                        local_username=local_username,
                                        local_password=local_password,
                                        remote_username=remote_username,
                                        remote_password=remote_password,
                                        connection_type=connection_type)

    def get_remote_interface(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityRemoteInterfaceList, _id=_id, name=name, **filters)

    def get_replication_interface(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityReplicationInterfaceList, _id=_id, name=name, **filters)

    def create_replication_interface(self, sp, ip_port, ip_address,
                                     netmask=None, v6_prefix_length=None,
                                     gateway=None, vlan_id=None):
        """
        Creates a replication interface.

        :param sp: `UnityStorageProcessor` object. Storage processor on which
            the replication interface is running.
        :param ip_port: `UnityIpPort` object. Physical port or link aggregation
            on the storage processor on which the interface is running.
        :param ip_address: IP address of the replication interface.
        :param netmask: IPv4 netmask for the replication interface, if it uses
            an IPv4 address.
        :param v6_prefix_length: IPv6 prefix length for the interface, if it
            uses an IPv6 address.
        :param gateway: IPv4 or IPv6 gateway address for the replication
            interface.
        :param vlan_id: VLAN identifier for the interface.
        :return: the newly create replication interface.
        """
        return UnityReplicationInterface.create(
            self._cli, sp, ip_port, ip_address, netmask=netmask,
            v6_prefix_length=v6_prefix_length, gateway=gateway,
            vlan_id=vlan_id)

    def get_replication_session(self, _id=None, name=None,
                                src_resource_id=None, dst_resource_id=None,
                                **filters):
        return self._get_unity_rsc(
            UnityReplicationSessionList, _id=_id, name=name,
            src_resource_id=src_resource_id, dst_resource_id=dst_resource_id,
            **filters)

    def get_import_session(self, _id=None, name=None, **filters):
        return self._get_unity_rsc(
            UnityImportSessionList, _id=_id, name=name, **filters)

    def create_alert_snmp_config(self, target_address, auth_protocol=None,
                                 username=None, auth_password=None,
                                 priv_protocol=None, priv_password=None,
                                 snmp_version=None, community=None):
        if not (community or username):
            raise storops.exception.UnityPolicyInvalidParametersError()
        alert = UnityAlertConfigSNMPTarget.create(self._cli, target_address,
                                                  auth_protocol=auth_protocol,
                                                  username=username,
                                                  auth_password=auth_password,
                                                  priv_protocol=priv_protocol,
                                                  priv_password=priv_password,
                                                  snmp_version=snmp_version,
                                                  community=community)
        return alert

    def get_alert_snmp_config(self, _id=None, **filters):
        return self._get_unity_rsc(UnityAlertConfigSNMPTargetList,
                                   _id=_id, **filters)

    def get_job(self, _id=None, **filters):
        return self._get_unity_rsc(UnityJobList, _id=_id, **filters)

    def get_alert(self, _id=None, **filters):
        return self._get_unity_rsc(UnityAlertList, _id=_id, **filters)

    def create_snap_schedule(self, name, rules,
                             is_sync_replicated=None,
                             skip_sync_to_remote_system=None):
        """ Creates snapshot schedule.
        :param name: Name of new schedule.
        :param rules: Rules that apply to the snapshot schedule, as defined by
            the `UnitySnapScheduleRule` resource type. Each value is a
            `UnitySnapScheduleRule` instance.
        :param is_sync_replicated: Indicates that all operations on the
            snapshot schedule will be synchronously replicated to the peer
            system.
        :param skip_sync_to_remote_system: For internal system use only. Skip
            the invocation of the snapshot schedule creation method with the
            same parameters on the remote system. If the method is invoked by
            the user, this attribute is not required. The value should be true
            when the operation is executed from a remote system, to prevent
            from syncing it back to the original storage.
        :return: the created `UnitySnapSchedule` instance.
        """
        schedule = UnitySnapScheduleList.get(self._cli, name=name)
        if schedule:
            raise storops.exception.UnitySnapScheduleNameInUseError()
        else:
            schedule = UnitySnapSchedule.create(
                self._cli, name, rules, is_sync_replicated=is_sync_replicated,
                skip_sync_to_remote_system=skip_sync_to_remote_system)

        return schedule

    def get_snap_schedule(self, _id=None, **filters):
        return self._get_unity_rsc(UnitySnapScheduleList, _id=_id, **filters)


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


class UnityBattery(UnityResource):
    @classmethod
    def get_nested_properties(cls):
        return (
            'parent_storage_processor.name',
        )


class UnityBatteryList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityBattery


class UnityDae(UnityResource):
    pass


class UnityDaeList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityDae


class UnityLcc(UnityResource):
    pass


class UnityLccList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityLcc


class UnityMemoryModule(UnityResource):
    pass


class UnityMemoryModuleList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityMemoryModule


class UnityPowerSupply(UnityResource):
    @classmethod
    def get_nested_properties(cls):
        return (
            'parent_dae.name',
            'parent_dpe.name',
            'storage_processor.name',
        )


class UnityPowerSupplyList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityPowerSupply


class UnitySsc(UnityResource):
    pass


class UnitySscList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySsc


class UnitySsd(UnityResource):
    pass


class UnitySsdList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySsd


class UnityFan(UnityResource):
    @classmethod
    def get_nested_properties(cls):
        return (
            'parent_dae.name',
            'parent_dpe.name',
        )


class UnityFanList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityFan


class UnityLicense(UnityResource):
    pass


class UnityLicenseList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityLicense


class UnityFeature(UnityResource):
    pass


class UnityFeatureList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityFeature


class UnityMgmtInterface(UnityResource):
    pass


class UnityMgmtInterfaceList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityMgmtInterface


class UnitySystemCapacity(UnityResource):
    pass


class UnitySystemCapacityList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySystemCapacity


class UnitySystemTierCapacity(UnityAttributeResource):
    pass


class UnitySystemTierCapacityList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySystemTierCapacity
