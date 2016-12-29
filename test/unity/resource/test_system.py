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
    StorageResourceTypeEnum, DNSServerOriginEnum, TierTypeEnum
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
from storops.unity.resource.metric import UnityMetricQueryResultList, \
    UnityMetricRealTimeQueryList
from storops.unity.resource.nas_server import UnityNasServer, \
    UnityNasServerList
from storops.unity.resource.nfs_server import UnityNfsServerList
from storops.unity.resource.nfs_share import UnityNfsShareList
from storops.unity.resource.pool import UnityPoolList
from storops.unity.resource.port import UnityFcPortList

from storops.unity.resource.lun import UnityLun
from storops.unity.resource.lun import UnityLunList
from storops.unity.resource.port import UnityIpPortList, \
    UnityEthernetPortList, UnityIscsiPortalList
from storops.unity.resource.snap import UnitySnapList
from storops.unity.resource.sp import UnityStorageProcessor, \
    UnityStorageProcessorList
from storops.unity.resource.system import UnitySystemList, UnitySystem, \
    UnityDpeList, UnityDpe, UnityVirusChecker, UnityVirusCheckerList, \
    UnityBasicSystemInfo, UnityBasicSystemInfoList, UnitySystemTime, \
    UnityNtpServer
from storops.unity.resource.vmware import UnityCapabilityProfileList
from test.unity.rest_mock import t_rest, patch_rest, t_unity

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
    def test_create_cg(self):
        lun1 = UnityLun(cli=t_rest(), _id='sv_3339')
        lun2 = UnityLun(cli=t_rest(), _id='sv_3340')
        unity = t_unity()
        cg = unity.create_cg('Muse', lun_list=[lun1, lun2])
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

    @patch_rest
    def test_get_file_port(self):
        unity = UnitySystem(cli=t_rest("4.1.0"))
        ports = unity.get_file_port()
        assert_that(len(ports), equal_to(10))

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

        time.sleep(1.5)
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
