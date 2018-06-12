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

import datetime
import time
from unittest import TestCase

from hamcrest import assert_that, equal_to, instance_of, only_contains, \
    raises, contains_string, is_in, has_items, none

from storops.exception import UnityResourceNotFoundError, \
    UnityHostNameInUseError, UnityActionNotAllowedError
from storops.lib.resource import ResourceList
from storops.unity.enums import EnclosureTypeEnum, DiskTypeEnum, HealthEnum, \
    HostTypeEnum, ServiceLevelEnum, ServiceLevelEnumList, \
    StorageResourceTypeEnum, DNSServerOriginEnum, TierTypeEnum, \
    RaidTypeEnum, RaidStripeWidthEnum, StoragePoolTypeEnum, DiskTypeEnumList, \
    SpeedValuesEnum, ConnectorTypeEnum, FeatureStateEnum, \
    InterfaceConfigModeEnum, IpProtocolVersionEnum
from storops.unity.resource.cifs_server import UnityCifsServerList
from storops.unity.resource.cifs_share import UnityCifsShareList, \
    UnityCifsShare
from storops.unity.resource.disk import UnityDisk
from storops.unity.resource.dns_server import UnityFileDnsServerList
from storops.unity.resource.filesystem import UnityFileSystemList, \
    UnityFileSystem
from storops.unity.resource.health import UnityHealth
from storops.unity.resource.host import UnityHostInitiator, \
    UnityHostInitiatorList, UnityHost, UnityHostList
from storops.unity.resource.interface import UnityFileInterfaceList
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.lun import UnityLunList
from storops.unity.resource.metric import UnityMetricQueryResultList, \
    UnityMetricRealTimeQueryList
from storops.unity.resource.nas_server import UnityNasServer, \
    UnityNasServerList
from storops.unity.resource.nfs_server import UnityNfsServerList
from storops.unity.resource.nfs_share import UnityNfsShareList
from storops.unity.resource.pool import UnityPoolList, \
    RaidGroupParameter, UnityPool
from storops.unity.resource.port import UnityFcPortList
from storops.unity.resource.port import UnityIpPortList, \
    UnityEthernetPortList, UnityIscsiPortalList
from storops.unity.resource.snap import UnitySnapList
from storops.unity.resource.sp import UnityStorageProcessor, \
    UnityStorageProcessorList
from storops.unity.resource.system import UnitySystemList, UnitySystem, \
    UnityDpeList, UnityDpe, UnityVirusChecker, UnityVirusCheckerList, \
    UnityBasicSystemInfo, UnityBasicSystemInfoList, UnitySystemTime, \
    UnityNtpServer, UnityDae, UnityFeature, UnityMgmtInterfaceList, \
    UnitySystemCapacityList, \
    UnitySystemTierCapacity, UnityIscsiNodeList
from storops.unity.resource.vmware import UnityCapabilityProfileList
from storops_test.unity.rest_mock import t_rest, patch_rest, t_unity

__author__ = 'Cedric Zhuang'


class UnitySystemTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        system = UnitySystem(cli=t_rest())
        assert_that(system.existed, equal_to(True))
        assert_that(system.health, instance_of(UnityHealth))
        assert_that(system.name, equal_to('FNM00151200215'))
        assert_that(system.model, equal_to('Unity 500'))
        assert_that(system.serial_number, equal_to('FNM00151200215'))
        assert_that(system.internal_model, equal_to('OBERON 25 DRIVE CHASSIS'))
        assert_that(system.platform, equal_to('Oberon_DualSP'))
        assert_that(system.mac_address, equal_to('08:00:1B:FF:EA:CD'))
        assert_that(system.is_eula_accepted, equal_to(True))
        assert_that(system.is_upgrade_complete, equal_to(True))
        assert_that(system.is_auto_failback_enabled, equal_to(True))
        assert_that(system.current_power, equal_to(469))
        assert_that(system.avg_power, equal_to(474))

    @patch_rest
    def test_init_by_ip(self):
        system = UnitySystem('10.244.223.66', 'admin', 'Password123!')
        assert_that(system.model, equal_to('Unity 500'))

    @patch_rest
    def test_get_all(self):
        systems = UnitySystemList(cli=t_rest())
        assert_that(len(systems), equal_to(1))

    @patch_rest
    def test_get_sp_all(self):
        unity = t_unity()
        sps = unity.get_sp()
        assert_that(sps, instance_of(UnityStorageProcessorList))
        assert_that(len(sps), equal_to(2))

    @patch_rest
    def test_get_spa(self):
        unity = t_unity()
        sp = unity.get_sp('spa')
        assert_that(sp, instance_of(UnityStorageProcessor))
        assert_that(sp.get_id(), equal_to('spa'))

    @patch_rest
    def test_get_capability_profile_service_levels(self):
        unity = t_unity()
        level_s = ServiceLevelEnum.SILVER
        level_p = ServiceLevelEnum.PLATINUM
        cp = unity.get_capability_profile(service_levels=[level_s, level_p])
        assert_that(cp, instance_of(UnityCapabilityProfileList))
        assert_that(len(cp), 2)

        # use Enum or EnumList are both ok
        cp2 = unity.get_capability_profile(service_levels=level_s)
        assert_that(cp2, instance_of(UnityCapabilityProfileList))
        assert_that(len(cp2), 1)
        assert_that(cp2[0].existed, equal_to(True))

        level_enum_list = ServiceLevelEnumList.parse([level_s, level_p])
        assert_that(level_enum_list, instance_of(ServiceLevelEnumList))
        cp3 = unity.get_capability_profile(service_levels=level_enum_list)
        assert_that(cp3, instance_of(UnityCapabilityProfileList))
        assert_that(len(cp3), 2)
        assert_that(cp3[0].existed, equal_to(True))

    @patch_rest
    def test_get_capability_profile_usage_tags(self):
        unity = t_unity()
        tag = "capacity"
        cp = unity.get_capability_profile(usage_tags=tag)
        assert_that(cp, instance_of(UnityCapabilityProfileList))
        assert_that(len(cp), 1)
        assert_that(cp[0].existed, equal_to(True))
        assert_that(tag, is_in(cp[0].usage_tags))

        cp2 = unity.get_capability_profile(usage_tags=[tag])
        assert_that(cp2, instance_of(UnityCapabilityProfileList))
        assert_that(len(cp2), 1)
        assert_that(cp2[0].existed, equal_to(True))
        assert_that(tag, is_in(cp2[0].usage_tags))

        # None tags will not pass to rest url
        # it's same with get_capability_profile()
        cp3 = unity.get_capability_profile(usage_tags=None)
        assert_that(cp3, instance_of(UnityCapabilityProfileList))
        assert_that(len(cp3), 2)
        assert_that(cp3[0].existed, equal_to(True))

    @patch_rest
    def test_get_capability_profile_not_found(self):
        unity = t_unity()
        cp = unity.get_capability_profile(service_levels=[5])
        assert_that(cp, instance_of(UnityCapabilityProfileList))
        assert_that(len(cp), equal_to(0))

    @patch_rest
    def test_get_sp_by_name(self):
        unity = t_unity()
        sp = unity.get_sp(name='SP A')
        assert_that(sp, instance_of(UnityStorageProcessor))
        assert_that(sp.id, equal_to('spa'))

    @patch_rest
    def test_get_lun_list(self):
        unity = t_unity()
        lun_list = unity.get_lun()
        assert_that(lun_list, instance_of(UnityLunList))
        assert_that(len(lun_list), equal_to(5))

    @patch_rest
    def test_create_host(self):
        unity = t_unity()
        host = unity.create_host("Hello")
        assert_that(host, instance_of(UnityHost))
        assert_that(host.id, equal_to('Host_11'))

    @patch_rest
    def test_create_host_existed(self):
        unity = t_unity()

        def f():
            # the 'flocker-3' is the Host_10 name
            unity.create_host("flocker-3")

        assert_that(f, raises(UnityHostNameInUseError))

    @patch_rest
    def test_get_portal_list(self):
        unity = t_unity()
        portals = unity.get_iscsi_portal()
        assert_that(portals, instance_of(UnityIscsiPortalList))

    @patch_rest
    def test_create_iscsi_portal(self):
        unity = t_unity()
        portal = unity.create_iscsi_portal(
            ethernet_port='spa_eth3', ip="10.244.213.244",
            netmask="255.255.255.0", vlan=133, gateway="10.244.213.1")
        assert_that(portal.id, equal_to('if_4'))

    @patch_rest
    def test_get_ethernet_list(self):
        unity = t_unity()
        ports = unity.get_ethernet_port()
        assert_that(ports, instance_of(UnityEthernetPortList))
        assert_that(len(ports), equal_to(8))

    @patch_rest
    def test_get_host_list(self):
        unity = t_unity()
        hosts = unity.get_host()
        assert_that(hosts, instance_of(UnityHostList))
        assert_that(len(hosts), equal_to(7))

    @patch_rest
    def test_get_initiators(self):
        unity = t_unity()
        initiators = unity.get_initiator()
        assert_that(initiators, instance_of(UnityHostInitiatorList))
        assert_that(len(initiators), equal_to(4))

    @patch_rest
    def test_get_initiator_by_id(self):
        unity = t_unity()
        initiator = unity.get_initiator(_id="HostInitiator_2")
        assert_that(initiator, instance_of(UnityHostInitiator))
        assert_that(initiator.id, equal_to("HostInitiator_2"))

    @patch_rest
    def test_get_initiator_by_name(self):
        unity = t_unity()
        wwn = "50:00:14:40:47:B0:0C:44:50:00:14:42:D0:0C:44:10"
        filtered = unity.get_initiator(initiator_id=wwn)
        assert_that(len(filtered), equal_to(1))
        assert_that(filtered, instance_of(UnityHostInitiatorList))
        initiator = filtered.first_item
        assert_that(initiator, instance_of(UnityHostInitiator))
        assert_that(initiator.existed, equal_to(True))
        assert_that(initiator.initiator_id, equal_to(wwn))

    @patch_rest
    def test_get_pools(self):
        unity = t_unity()
        pools = unity.get_pool()
        assert_that(pools, instance_of(UnityPoolList))
        assert_that(len(pools), equal_to(2))

    @patch_rest
    def test_create_pool(self):
        unity = t_unity()
        disk_group = unity.get_disk_group(_id='dg_15')
        raid_group_0 = RaidGroupParameter(
            disk_group=disk_group,
            disk_num=3, raid_type=RaidTypeEnum.RAID5,
            stripe_width=RaidStripeWidthEnum.BEST_FIT)
        raid_groups = [raid_group_0]
        pool = unity.create_pool(
            name='test_pool', description='Unity test pool.',
            raid_groups=raid_groups, alert_threshold=15,
            is_harvest_enabled=True, is_snap_harvest_enabled=True,
            pool_harvest_high_threshold=80, pool_harvest_low_threshold=40,
            snap_harvest_high_threshold=80, snap_harvest_low_threshold=40,
            is_fast_cache_enabled=True, is_fastvp_enabled=True,
            pool_type=StoragePoolTypeEnum.DYNAMIC)
        assert_that(pool, instance_of(UnityPool))

    @patch_rest
    def test_get_snaps_all(self):
        unity = t_unity()
        snaps = unity.get_snap()
        assert_that(snaps, instance_of(UnitySnapList))
        assert_that(len(snaps), equal_to(3))

    @patch_rest
    def test_get_snap_by_name(self):
        unity = t_unity()
        snap = unity.get_snap(name='2016-03-15_10:56:08')
        assert_that(snap.name, equal_to('2016-03-15_10:56:08'))
        assert_that(snap.existed, equal_to(True))

    @patch_rest
    def test_get_nas_servers(self):
        unity = t_unity()
        nas_servers = unity.get_nas_server()
        assert_that(nas_servers, instance_of(UnityNasServerList))
        assert_that(len(nas_servers), equal_to(3))

    @patch_rest
    def test_create_nas_server(self):
        unity = t_unity()
        sp = unity.get_sp(_id='spa')
        pool = unity.get_pool(_id='pool_1')
        nas_server = unity.create_nas_server('nas3', sp, pool)
        assert_that(nas_server.existed, equal_to(True))

    @patch_rest
    def test_auto_balance_sp_one_sp(self):
        unity = t_unity()

        @patch_rest(output='auto_balance_sp_one_sp.json')
        def inner():
            sp = unity._auto_balance_sp()
            assert_that(sp.get_id(), equal_to('spa'))

        unity._auto_balance_sp()
        inner()

    @patch_rest
    def test_auto_balance_sp_to_spb(self):
        unity = t_unity()
        sp = unity._auto_balance_sp()
        assert_that(sp.get_id(), equal_to('spb'))

    @patch_rest
    def test_auto_balance_sp_to_spa(self):
        unity = t_unity()

        @patch_rest(output='auto_balance_sp_to_spa.json')
        def inner():
            sp = unity._auto_balance_sp()
            assert_that(sp.get_id(), equal_to('spa'))

        unity._auto_balance_sp()
        inner()

    @patch_rest
    def test_get_ip_ports(self):
        unity = t_unity()
        ip_ports = unity.get_ip_port()
        assert_that(ip_ports, instance_of(UnityIpPortList))
        assert_that(len(ip_ports), equal_to(8))

    @patch_rest
    def test_get_file_interface(self):
        unity = t_unity()
        fi_list = unity.get_file_interface()
        assert_that(fi_list, instance_of(UnityFileInterfaceList))
        assert_that(len(fi_list), equal_to(1))

    @patch_rest
    def test_get_cifs_server(self):
        unity = t_unity()
        cifs_servers = unity.get_cifs_server()
        assert_that(cifs_servers, instance_of(UnityCifsServerList))
        assert_that(len(cifs_servers), equal_to(1))

    @patch_rest
    def test_get_nfs_server(self):
        unity = t_unity()
        nfs_servers = unity.get_nfs_server()
        assert_that(nfs_servers, instance_of(UnityNfsServerList))
        assert_that(len(nfs_servers), equal_to(1))

    @patch_rest
    def test_get_dns_server(self):
        unity = t_unity()
        dns_servers = unity.get_dns_server()
        assert_that(dns_servers, instance_of(UnityFileDnsServerList))
        assert_that(len(dns_servers), equal_to(1))

    @patch_rest
    def test_get_file_system(self):
        unity = t_unity()
        filesystems = unity.get_filesystem()
        assert_that(filesystems, instance_of(UnityFileSystemList))
        assert_that(len(filesystems), equal_to(3))

    @patch_rest
    def test_get_cifs_share(self):
        unity = t_unity()
        shares = unity.get_cifs_share()
        assert_that(shares, instance_of(UnityCifsShareList))
        assert_that(len(shares), equal_to(1))

    @patch_rest
    def test_get_nfs_share(self):
        unity = t_unity()
        shares = unity.get_nfs_share()
        assert_that(shares, instance_of(UnityNfsShareList))
        assert_that(len(shares), equal_to(2))

    @patch_rest
    def test_get_host_by_address_found(self):
        unity = t_unity()
        host = unity.get_host(address='8.8.8.8')
        assert_that(host.type, equal_to(HostTypeEnum.SUBNET))

    @patch_rest
    def test_get_host_by_address_not_found(self):
        unity = t_unity()
        hosts = unity.get_host(address='8.8.8.9')
        assert_that(len(hosts), equal_to(0))

    @patch_rest
    def test_system_info(self):
        unity = t_unity()
        assert_that(unity.info, instance_of(UnityBasicSystemInfo))

    @patch_rest
    def test_system_get_cifs_share_by_name(self):
        unity = t_unity()
        cs = unity.get_cifs_share(name='cs1')
        assert_that(cs, instance_of(UnityCifsShare))
        assert_that(cs.name, equal_to('cs1'))

    @patch_rest
    def test_system_get_fs_by_name_not_found(self):
        def f():
            unity = t_unity()
            unity.get_filesystem(name='not_found')

        assert_that(f, raises(UnityResourceNotFoundError,
                              'UnityFileSystem:not_found'))

    @patch_rest
    def test_get_doc_enum_member(self):
        unity = t_unity()
        doc = unity.get_doc(HealthEnum.NON_RECOVERABLE)
        assert_that(doc, contains_string('OK But Minor Warning'))

    @patch_rest
    def test_get_doc_enum(self):
        unity = t_unity()
        doc = unity.get_doc(HealthEnum)
        assert_that(doc, contains_string('OK But Minor Warning'))

    @patch_rest
    def test_get_doc_resource(self):
        unity = t_unity()
        doc = unity.get_doc(unity.get_snap())
        assert_that(doc, contains_string(
            'For a file system or VMware NFS datastore'))

    @patch_rest
    def test_get_fc_port(self):
        unity = t_unity()
        fi_list = unity.get_fc_port()
        assert_that(fi_list, instance_of(UnityFcPortList))
        assert_that(len(fi_list), equal_to(12))

    @patch_rest(output='fc_port_not_supported.json')
    def test_get_fc_port_not_supported(self):
        unity = t_unity(version='4.1.2')
        fc = unity.get_fc_port()
        assert_that(len(fc), equal_to(0))

    @patch_rest
    def test_get_io_limit_policy_by_name(self):
        unity = t_unity()
        name = 'Density_1100_KBPS'
        policy = unity.get_io_limit_policy(name=name)
        assert_that(policy.name, equal_to(name))

    @patch_rest
    def test_get_io_limit_policy_all(self):
        unity = t_unity()
        policies = unity.get_io_limit_policy()
        assert_that(len(policies), equal_to(6))

    @patch_rest
    def test_create_kbps_policy(self):
        unity = t_unity()
        policy = unity.create_io_limit_policy(
            'max_kbps_1234', max_kbps=1234, description='storops')
        assert_that(policy.name, equal_to('max_kbps_1234'))
        setting = policy.io_limit_rule_settings[0]
        assert_that(setting.max_kbps, equal_to(1234))

    @patch_rest
    def test_create_burst_policy(self):
        unity = t_unity()
        policy = unity.create_io_limit_policy(
            'burst_policy', description='storops', max_iops=1000,
            max_kbps=20480, burst_rate=50, burst_time=10, burst_frequency=2)
        assert_that(policy.name, equal_to('burst_policy'))
        setting = policy.io_limit_rule_settings[0]
        assert_that(setting.burst_rate, equal_to(50))
        assert_that(setting.burst_time, equal_to(10))
        assert_that(setting.burst_frequency, equal_to(2))

    @patch_rest
    def test_create_cg(self):
        lun1 = UnityLun(cli=t_rest(), _id='sv_3339')
        lun2 = UnityLun(cli=t_rest(), _id='sv_3340')
        unity = t_unity()
        cg = unity.create_cg('Muse', lun_add=[lun1, lun2])
        assert_that(cg.name, equal_to('Muse'))
        assert_that(len(cg.luns), equal_to(2))

    @patch_rest
    def test_get_cg_list(self):
        cg_list = t_unity().get_cg()
        assert_that(len(cg_list), equal_to(2))

    @patch_rest
    def test_get_cg_by_name(self):
        cg = t_unity().get_cg(name='Nike')
        assert_that(cg.name, equal_to('Nike'))

    @patch_rest
    def test_get_cg_by_id(self):
        cg = t_unity().get_cg(_id='res_13')
        assert_that(cg.id, equal_to('res_13'))
        cg_type = StorageResourceTypeEnum.CONSISTENCY_GROUP
        assert_that(cg.type, equal_to(cg_type))

    @patch_rest
    def test_system_time(self):
        assert_that(t_unity().system_time.year, equal_to(2016))

    @patch_rest
    def test_set_system_time(self):
        unity = t_unity()
        st = unity.system_time
        ret = unity.set_system_time(new_time=st)
        assert_that(ret, instance_of(datetime.datetime))
        assert_that(ret.microsecond, equal_to(534000))

    @patch_rest
    def test_set_ntp_server(self):
        ret = t_unity().add_ntp_server('10.245.54.154', '10.245.54.153')
        assert_that(ret, has_items('10.245.54.152', '10.245.54.153'))

    @patch_rest
    def test_remove_ntp_server(self):
        ret = t_unity().remove_ntp_server('10.245.54.153')
        assert_that(ret, has_items('10.245.54.152', '10.245.54.153'))

    @patch_rest
    def test_clear_ntp_server(self):
        ret = t_unity().clear_ntp_server()
        assert_that(ret, has_items('10.245.54.152', '10.245.54.153'))

    @patch_rest
    def test_list_ntp_servers(self):
        assert_that(t_unity().ntp_server,
                    has_items('10.245.54.152', '10.245.54.153'))

    @patch_rest
    def test_delete_singleton(self):
        def f():
            t_unity()._ntp_server.delete()

        assert_that(f, raises(UnityActionNotAllowedError, 'not allowed'))

    @patch_rest
    def test_list_dns_server(self):
        dns_server = t_unity().dns_server
        assert_that(dns_server.id, equal_to('0'))
        assert_that(dns_server.origin, equal_to(DNSServerOriginEnum.DHCP))
        assert_that(dns_server.addresses,
                    has_items('10.245.177.15', '10.245.177.16'))

    @patch_rest
    def test_add_dns_server(self):
        ret = t_unity().add_dns_server('8.8.8.8', '9.9.9.9')
        assert_that(ret, has_items('10.245.177.15', '10.245.177.16'))

    @patch_rest
    def test_remove_dns_server(self):
        ret = t_unity().remove_dns_server('8.8.8.8', '9.9.9.9')
        assert_that(ret, has_items('10.245.177.15', '10.245.177.16'))

    @patch_rest
    def test_clear_dns_server(self):
        ret = t_unity().clear_dns_server()
        assert_that(ret, has_items('10.245.177.15', '10.245.177.16'))

    @patch_rest
    def test_get_link_aggregation_list(self):
        la_list = t_unity().get_link_aggregation()
        assert_that(len(la_list), equal_to(2))

    @patch_rest
    def test_get_disk(self):
        disks = t_unity().get_disk(tier_type=TierTypeEnum.EXTREME_PERFORMANCE)
        assert_that(len(disks), equal_to(4))

    @patch_rest
    def test_get_link_aggregation_by_name(self):
        cg = t_unity().get_link_aggregation(name='SP A Link Aggregation 2')
        assert_that(cg.name, equal_to('SP A Link Aggregation 2'))

    @patch_rest
    def test_get_link_aggregation_by_id(self):
        cg = t_unity().get_link_aggregation(_id='spa_la_2')
        assert_that(cg.id, equal_to('spa_la_2'))

    @patch_rest(output='link_aggregation_not_supported.json')
    def test_get_link_aggregation_not_supported(self):
        unity = t_unity(version='4.1.2')
        la = unity.get_link_aggregation()
        assert_that(len(la), equal_to(0))

    @patch_rest
    def test_get_file_port(self):
        unity = UnitySystem(cli=t_rest("4.1.0"))
        ports = unity.get_file_port()
        assert_that(len(ports), equal_to(6))

    @patch_rest
    def test_get_file_port_la_unsupported(self):
        unity = UnitySystem(cli=t_rest("4.0.0"))
        ports = unity.get_file_port()
        assert_that(len(ports), equal_to(8))

    @patch_rest
    def test_enable_performance_statistics(self):
        unity = UnitySystem('10.244.223.61')
        assert_that(unity.is_perf_stats_enabled(), equal_to(False))

        queries = unity.enable_perf_stats(1)
        assert_that(queries, instance_of(UnityMetricRealTimeQueryList))

        time.sleep(5)
        assert_that(unity.is_perf_stats_enabled(), equal_to(True))
        assert_that(unity._cli.curr_counter,
                    instance_of(UnityMetricQueryResultList))

        unity.disable_perf_stats()
        assert_that(unity.is_perf_stats_enabled(), equal_to(False))
        assert_that(unity._cli.curr_counter, none())
        assert_that(unity._cli.prev_counter, none())

    @patch_rest
    def test_enable_persist_perf_stats(self):
        unity = UnitySystem('10.244.223.61')
        assert_that(unity.is_perf_stats_persisted(), equal_to(False))

        unity.enable_persist_perf_stats()
        assert_that(unity.is_perf_stats_persisted(), equal_to(True))

        unity.disable_persist_perf_stats()
        assert_that(unity.is_perf_stats_persisted(), equal_to(False))

    @patch_rest
    def test_default_rsc_clz_list_with_perf_stats(self):
        rsc_list_collection = t_unity()._default_rsc_list_with_perf_stats()
        clz_list = ResourceList.get_rsc_clz_list(rsc_list_collection)
        assert_that(clz_list, has_items(UnityDisk, UnityLun, UnityFileSystem))

    @patch_rest
    def test_get_tenant(self):
        unity = t_unity()
        tenant = unity.get_tenant()
        assert_that(len(tenant), equal_to(3))

    @patch_rest
    def test_get_tenant_use_vlan(self):
        unity = t_unity()
        tenant = unity.get_tenant_use_vlan(4)
        assert_that(tenant.id, equal_to('tenant_4'))

    @patch_rest
    def test_get_tenant_use_vlan_not_found(self):
        unity = t_unity()
        tenant = unity.get_tenant_use_vlan(5)
        assert_that(tenant, equal_to(None))

    @patch_rest
    def test_create_tenant(self):
        unity = t_unity()
        unity.create_tenant(
            'test', uuid='173ca6c3-5952-427d-82a6-df88f49e3926',
            vlans=[3])

    @patch_rest(output='system/license_upload.json')
    def test_upload_license(self):
        unity = t_unity()
        unity.upload_license(license="license.lic")

    @patch_rest
    def test_get_iscsi_node(self):
        unity = t_unity()
        nodes = unity.get_iscsi_node()
        assert_that(nodes, instance_of(UnityIscsiNodeList))
        assert_that(len(nodes), equal_to(4))

    @patch_rest
    def test_get_mgmt_interface(self):
        unity = t_unity()
        interfaces = unity.get_mgmt_interface()
        assert_that(interfaces, instance_of(UnityMgmtInterfaceList))
        assert_that(len(interfaces), equal_to(1))

    @patch_rest
    def test_get_system_capacity(self):
        unity = t_unity()
        capacities = unity.get_system_capacity()
        assert_that(capacities, instance_of(UnitySystemCapacityList))
        assert_that(len(capacities), equal_to(1))


class UnityDpeTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        dpe = UnityDpe('dpe', cli=t_rest())
        assert_that(dpe.existed, equal_to(True))
        assert_that(dpe.health, instance_of(UnityHealth))
        assert_that(dpe.needs_replacement, equal_to(False))
        assert_that(dpe.slot_number, equal_to(0))
        assert_that(dpe.name, equal_to('DPE'))
        assert_that(dpe.manufacturer, equal_to(''))
        assert_that(dpe.model, equal_to('OBERON 25 DRIVE CHASSIS'))
        assert_that(dpe.emc_part_number, equal_to('100-542-901-05'))
        assert_that(dpe.emc_serial_number, equal_to('CF2CV150500005'))
        assert_that(dpe.vendor_part_number, equal_to(''))
        assert_that(dpe.vendor_serial_number, equal_to(''))
        assert_that(dpe.bus_id, equal_to(0))
        assert_that(dpe.current_power, equal_to(429))
        assert_that(dpe.avg_power, equal_to(397))
        assert_that(dpe.max_power, equal_to(429))
        assert_that(dpe.current_temperature, equal_to(26))
        assert_that(dpe.avg_temperature, equal_to(26))
        assert_that(dpe.max_temperature, equal_to(26))
        assert_that(dpe.current_speed, equal_to(12000000000))
        assert_that(dpe.max_speed, equal_to(12000000000))
        assert_that(dpe.parent_system, instance_of(UnitySystem))
        assert_that(dpe.enclosure_type,
                    equal_to(EnclosureTypeEnum.MIRANDA_12G_SAS_DPE))
        assert_that(dpe.drive_types,
                    only_contains(DiskTypeEnum.SAS, DiskTypeEnum.SAS_FLASH_2))

    @patch_rest
    def test_get_all(self):
        dpe_list = UnityDpeList(cli=t_rest())
        assert_that(len(dpe_list), equal_to(1))


class UnityVirusCheckerTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        checker = UnityVirusChecker('cava_2', cli=t_rest())
        assert_that(checker.existed, equal_to(True))
        assert_that(checker.nas_server, instance_of(UnityNasServer))
        assert_that(checker.is_enabled, equal_to(False))

    @patch_rest
    def test_get_all(self):
        checker_list = UnityVirusCheckerList(cli=t_rest())
        assert_that(len(checker_list), equal_to(1))


class UnityBasicSystemInfoTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        info = UnityBasicSystemInfo(t_rest())
        assert_that(info.id, equal_to('0'))
        assert_that(info.existed, equal_to(True))
        assert_that(info.name, equal_to('FNM00151200215'))
        assert_that(info.software_version, equal_to('4.1.0'))
        assert_that(info.earliest_api_version, equal_to('4.0'))
        assert_that(info.model, equal_to('Unity 500'))
        assert_that(info.api_version, equal_to("5.0"))

    @patch_rest
    def test_get_all(self):
        info_list = UnityBasicSystemInfoList(cli=t_rest())
        assert_that(len(info_list), equal_to(1))


class UnitySystemTimeTest(TestCase):
    @patch_rest
    def test_get_system_time(self):
        st = UnitySystemTime(t_rest()).time
        assert_that(st, instance_of(datetime.datetime))
        assert_that(st.year, equal_to(2016))
        assert_that(st.month, equal_to(11))
        assert_that(st.day, equal_to(14))
        assert_that(st.hour, equal_to(7))
        assert_that(st.minute, equal_to(23))
        assert_that(st.second, equal_to(53))


class UnityNtpServerTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        ntp_server = UnityNtpServer(cli=t_rest())
        assert_that(ntp_server.addresses,
                    has_items('10.245.54.152', '10.245.54.153'))


class UnityBatteryTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        batteries = t_unity().get_battery()
        assert_that(len(batteries), equal_to(2))
        battery0 = batteries[0]
        assert_that(battery0.id, equal_to("spa_bbu_0"))
        assert_that(battery0.health, instance_of(UnityHealth))
        assert_that(battery0.needs_replacement, equal_to(False))
        assert_that(battery0.parent, instance_of(dict))
        assert_that(battery0.slot_number, equal_to(0))
        assert_that(battery0.name, equal_to("SP A Battery 0"))
        assert_that(battery0.manufacturer, equal_to("ACBEL POLYTECH INC."))
        assert_that(battery0.model, equal_to("LITHIUM-ION, UNIVERSAL BOB"))
        assert_that(battery0.firmware_version, equal_to("073.91"))
        assert_that(battery0.emc_part_number, equal_to("078-000-128-02"))
        assert_that(battery0.emc_serial_number, equal_to("ACPJ5143800045"))
        assert_that(battery0.vendor_part_number, equal_to("SGD006-710G"))
        assert_that(battery0.vendor_serial_number, equal_to(""))
        assert_that(battery0.parent_storage_processor,
                    instance_of(UnityStorageProcessor))

    @patch_rest
    def test_get_nested_properties(self):
        batteries = t_unity().get_battery()
        assert_that(len(batteries), equal_to(2))
        battery0 = batteries[0]
        assert_that(battery0.parent_storage_processor.id, equal_to("spa"))
        assert_that(battery0.parent_storage_processor.name, equal_to("SP A"))


class UnityDaeTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        daes = t_unity().get_dae()
        assert_that(len(daes), equal_to(1))
        dae0 = daes[0]
        assert_that(dae0.id, equal_to("dae_0_1"))
        assert_that(dae0.enclosure_type,
                    equal_to(EnclosureTypeEnum.ANCHO_12G_SAS_DAE))
        assert_that(dae0.drive_types, instance_of(DiskTypeEnumList))
        assert_that(dae0.drive_types[0], DiskTypeEnum.NL_SAS)
        assert_that(dae0.health, instance_of(UnityHealth))
        assert_that(dae0.needs_replacement, equal_to(False))
        assert_that(dae0.parent, instance_of(dict))
        assert_that(dae0.slot_number, equal_to(1))
        assert_that(dae0.name, equal_to("DAE 0 1"))
        assert_that(dae0.manufacturer, equal_to(""))
        assert_that(dae0.model, equal_to("ANCHO LF 12G SAS DAE"))
        assert_that(dae0.emc_part_number, equal_to("100-900-000-04"))
        assert_that(dae0.emc_serial_number, equal_to("CF22W145100058"))
        assert_that(dae0.vendor_part_number, equal_to(""))
        assert_that(dae0.vendor_serial_number, equal_to(""))
        assert_that(dae0.bus_id, equal_to(0))
        assert_that(dae0.current_power, equal_to(110))
        assert_that(dae0.avg_power, equal_to(110))
        assert_that(dae0.max_power, equal_to(110))
        assert_that(dae0.current_temperature, equal_to(25))
        assert_that(dae0.avg_temperature, equal_to(25))
        assert_that(dae0.max_temperature, equal_to(25))
        assert_that(dae0.current_speed, equal_to(12000000000))
        assert_that(dae0.max_speed, equal_to(12000000000))
        assert_that(dae0.parent_system, instance_of(UnitySystem))


class UnityLccTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        lccs = t_unity().get_lcc()
        assert_that(len(lccs), equal_to(2))
        lcc = lccs[0]
        assert_that(lcc.id, equal_to("dae_0_1_lcc_a"))
        assert_that(lcc.health, instance_of(UnityHealth))
        assert_that(lcc.needs_replacement, equal_to(False))
        assert_that(lcc.parent, instance_of(dict))
        assert_that(lcc.slot_number, equal_to(0))
        assert_that(lcc.name, equal_to("DAE 0 1 Link Control Card A"))
        assert_that(lcc.manufacturer, equal_to(""))
        assert_that(lcc.model, equal_to("ANCHO 12G SAS LCC FRU ASSY"))
        assert_that(lcc.sas_expander_versions, equal_to(["2.20.0"]))
        assert_that(lcc.emc_part_number, equal_to("303-300-000C-02"))
        assert_that(lcc.emc_serial_number, equal_to("CF2W9145000032"))
        assert_that(lcc.vendor_part_number, equal_to(""))
        assert_that(lcc.vendor_serial_number, equal_to(""))
        assert_that(lcc.current_speed, equal_to(12000000000))
        assert_that(lcc.max_speed, equal_to(12000000000))
        assert_that(lcc.parent_dae, instance_of(UnityDae))


class UnityMemoryModuleTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        memory_modules = t_unity().get_memory_module()
        assert_that(len(memory_modules), equal_to(8))
        memory_module = memory_modules[0]
        assert_that(memory_module.id, equal_to("spa_mm_0"))
        assert_that(memory_module.health, instance_of(UnityHealth))
        assert_that(memory_module.needs_replacement, equal_to(False))
        assert_that(memory_module.slot_number, equal_to(0))
        assert_that(memory_module.name, equal_to("SP A Memory Module 0"))
        assert_that(memory_module.manufacturer, equal_to("Samsung"))
        assert_that(memory_module.model, equal_to("DDR4 SDRAM"))
        assert_that(memory_module.firmware_version, equal_to(""))
        assert_that(memory_module.size, equal_to(16))
        assert_that(memory_module.emc_part_number, equal_to("100-564-193-00"))
        assert_that(memory_module.emc_serial_number,
                    equal_to("80CE02151171BE4865"))
        assert_that(memory_module.vendor_part_number,
                    equal_to("M393A2G40DB0-CPB"))
        assert_that(memory_module.vendor_serial_number,
                    equal_to("71BE4865"))
        assert_that(memory_module.is_inserted, equal_to(True))
        assert_that(memory_module.parent_storage_processor,
                    instance_of(UnityStorageProcessor))


class UnityPowerSupplyTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        supplies = t_unity().get_power_supply()
        assert_that(len(supplies), equal_to(4))
        supply = supplies[0]

        assert_that(supply.id, equal_to("dae_0_1_ps_a0"))
        assert_that(supply.health, instance_of(UnityHealth))
        assert_that(supply.needs_replacement, equal_to(False))
        assert_that(supply.slot_number, equal_to(0))
        assert_that(supply.name, equal_to("DAE 0 1 Power Supply A0"))
        assert_that(supply.manufacturer, equal_to("ACBEL POLYTECH INC."))
        assert_that(supply.model, equal_to("Third Gen VE.400W, Dual +12V P/S"))
        assert_that(supply.firmware_version, equal_to("0421"))
        assert_that(supply.emc_serial_number, equal_to("AC7B7143200521"))
        assert_that(supply.vendor_part_number, equal_to("SGA001-710G"))
        assert_that(supply.vendor_serial_number, equal_to("AC7143202316"))
        assert_that(supply.emc_part_number, equal_to("071-000-553"))
        assert_that(supply.parent_dae, instance_of(UnityDae))
        assert_that(supply.storage_processor,
                    instance_of(UnityStorageProcessor))

    @patch_rest
    def test_get_nested_properties(self):
        supplies = t_unity().get_power_supply()
        assert_that(len(supplies), equal_to(4))

        supply0 = supplies[0]
        assert_that(supply0.parent_dae.id, equal_to('dae_0_1'))
        assert_that(supply0.parent_dae.name, equal_to('DAE 0 1'))
        assert_that(supply0.storage_processor.id, equal_to('spa'))
        assert_that(supply0.storage_processor.name, equal_to('SP A'))

        supply2 = supplies[2]
        assert_that(supply2.parent_dpe.id, equal_to('dpe'))
        assert_that(supply2.parent_dpe.name, equal_to('DPE'))


class UnitySasPortTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        ports = t_unity().get_sas_port()
        assert_that(len(ports), equal_to(4))
        port = ports[0]

        assert_that(port.id, equal_to("spa_sas0"))
        assert_that(port.health, instance_of(UnityHealth))
        assert_that(port.needs_replacement, equal_to(False))
        assert_that(port.name, equal_to("SP A SAS Port 0"))
        assert_that(port.port, equal_to(0))
        assert_that(port.current_speed, equal_to(SpeedValuesEnum._12Gbps))
        assert_that(port.connector_type,
                    equal_to(ConnectorTypeEnum.MINI_SAS_HD))
        assert_that(port.storage_processor, instance_of(UnityStorageProcessor))
        assert_that(port.parent_io_module, none())
        assert_that(port.parent_storage_processor,
                    instance_of(UnityStorageProcessor))


# TODO find a system with ssc
class UnitySscTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        sscs = t_unity().get_ssc()

        assert_that(len(sscs), equal_to(0))
        # ssc = sscs[0]
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))
        # assert_that(ssc.id, equal_to(""))


class UnitySsdTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        ssds = t_unity().get_ssd()

        ssd = ssds[0]
        assert_that(ssd.id, equal_to("spa_ssd"))
        assert_that(ssd.health, instance_of(UnityHealth))
        assert_that(ssd.needs_replacement, equal_to(False))
        assert_that(ssd.slot_number, equal_to(0))
        assert_that(ssd.name, equal_to("SP A Internal Disk"))
        assert_that(ssd.manufacturer, equal_to(""))
        assert_that(ssd.model, equal_to("Intel DC 3500 Series SSDs M.2"))
        assert_that(ssd.firmware_version, equal_to("G201EM05"))
        assert_that(ssd.emc_part_number, equal_to(
            "INTEL SSDSCKHB120G4M           118000040"))
        assert_that(ssd.emc_serial_number, equal_to("BTWM4CO00FTB"))
        assert_that(ssd.vendor_part_number, equal_to(""))
        assert_that(ssd.vendor_serial_number, equal_to(""))
        assert_that(ssd.parent_storage_processor, instance_of(
            UnityStorageProcessor))


class UnityFanTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        fans = t_unity().get_fan()
        assert_that(len(fans), equal_to(10))

        fan = fans[0]
        assert_that(fan.id, equal_to("dpe_fan_a0"))
        assert_that(fan.health, instance_of(UnityHealth))
        assert_that(fan.parent, instance_of(dict))
        assert_that(fan.slot_number, equal_to(0))
        assert_that(fan.name, equal_to("DPE Cooling Module A0"))
        assert_that(fan.emc_part_number, equal_to("100-542-054-05"))
        assert_that(fan.emc_serial_number, equal_to(""))
        assert_that(fan.manufacturer, equal_to(""))
        assert_that(fan.model, equal_to(""))
        assert_that(fan.vendor_part_number, equal_to(""))
        assert_that(fan.needs_replacement, equal_to(False))
        assert_that(fan.parent_dpe, instance_of(UnityDpe))
        assert_that(fan.parent_dpe.name, equal_to('DPE'))

    @patch_rest
    def test_get_nested_properties(self):
        fans = t_unity().get_fan()
        assert_that(len(fans), equal_to(10))

        fan = fans[0]
        assert_that(fan.parent_dpe.id, equal_to("dpe"))
        assert_that(fan.parent_dpe.name, equal_to("DPE"))
        assert_that(fan.parent_dae.id, equal_to("dae"))
        assert_that(fan.parent_dae.name, equal_to("DAE"))


class UnityLicenseTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        licenses = t_unity().get_license()

        assert_that(len(licenses), equal_to(20))

        license = licenses[0]
        assert_that(license.id, equal_to("ANTIVIRUS"))
        assert_that(license.name, equal_to("ANTIVIRUS"))
        assert_that(license.is_installed, equal_to(True))
        assert_that(license.version, equal_to("1.0"))
        assert_that(license.is_valid, equal_to(True))
        assert_that(license.issued, equal_to("2006-09-08T00:00:00.000Z"))
        assert_that(license.expires, equal_to("2017-06-30T00:00:00.000Z"))
        assert_that(license.is_permanent, equal_to(False))
        assert_that(license.feature, instance_of(UnityFeature))


class UnityFeatureTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        features = t_unity().get_feature()

        assert_that(len(features), equal_to(37))
        feature = features[0]
        assert_that(feature.id, equal_to("ADVANCED_STATIC_ROUTING"))
        assert_that(feature.name, equal_to("ADVANCED_STATIC_ROUTING"))
        assert_that(feature.state, equal_to(FeatureStateEnum.Enabled))
        assert_that(feature.reason, none())
        assert_that(feature.license, none())


class UnityMgmtInterface(TestCase):
    @patch_rest
    def test_get_properties(self):
        interfaces = t_unity().get_mgmt_interface()
        assert_that(len(interfaces), equal_to(1))

        interface = interfaces[0]
        assert_that(interface.id, equal_to('mgmt_ipv4'))
        assert_that(interface.config_mode,
                    equal_to(InterfaceConfigModeEnum.AUTO))
        assert_that(interface.protocol_version,
                    equal_to(IpProtocolVersionEnum.IPv4))
        assert_that(interface.ip_address, equal_to('10.245.101.39'))
        assert_that(interface.netmask, equal_to('255.255.255.0'))
        assert_that(interface.gateway, equal_to('10.245.101.1'))
        assert_that(interface.ethernet_port.id, equal_to('spb_mgmt'))


class UnitySystemCapacity(TestCase):
    @patch_rest
    def test_get_properties(self):
        capacities = t_unity().get_system_capacity()
        assert_that(len(capacities), equal_to(1))

        capacity = capacities[0]
        assert_that(capacity.id, equal_to('0'))
        assert_that(capacity.size_free, equal_to(9496172691456))
        assert_that(capacity.size_total, equal_to(9641664708608))
        assert_that(capacity.size_used, equal_to(145492017152))
        assert_that(capacity.compression_size_saved, equal_to(0))
        assert_that(capacity.compression_percent, equal_to(0))
        assert_that(capacity.compression_ratio, equal_to(1))
        assert_that(capacity.data_reduction_size_saved, equal_to(0))
        assert_that(capacity.data_reduction_percent, equal_to(0))
        assert_that(capacity.data_reduction_ratio, equal_to(1))
        assert_that(capacity.size_subscribed, equal_to(1018980990976))
        assert_that(capacity.tiers[0], instance_of(UnitySystemTierCapacity))
