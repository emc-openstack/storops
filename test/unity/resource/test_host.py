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

import ddt
from unittest import TestCase

from hamcrest import equal_to, assert_that, instance_of, raises, none, \
    only_contains
from storops.unity.resource.nfs_share import UnityNfsShare

from storops.exception import UnityHostIpInUseError, \
    UnityResourceNotFoundError, UnityHostInitiatorNotFoundError, \
    UnityHostInitiatorUnknownType, UnityAluAlreadyAttachedError, \
    UnityAttachAluExceedLimitError, UnitySnapAlreadyPromotedException, \
    SystemAPINotSupported
from storops.unity.enums import HostTypeEnum, HostManageEnum, \
    HostPortTypeEnum, HealthEnum, HostInitiatorTypeEnum, \
    HostInitiatorSourceTypeEnum, HostInitiatorIscsiTypeEnum
from storops.unity.resource.health import UnityHealth
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.host import UnityHost, UnityHostContainer, \
    UnityHostInitiator, UnityHostInitiatorList, UnityHostIpPortList, \
    UnityHostList, UnityHostIpPort, UnityHostInitiatorPathList, \
    UnityHostLun, UnityHostLunList
from storops.unity.resource.snap import UnitySnap
from storops.unity.resource.tenant import UnityTenant
from storops.unity.resource.vmware import UnityDataStoreList, UnityVmList
from test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


@ddt.ddt
class UnityHotTest(TestCase):
    @patch_rest
    def test_properties(self):
        host = UnityHost(_id='Host_1', cli=t_rest())
        assert_that(host.id, equal_to('Host_1'))
        assert_that(host.type, equal_to(HostTypeEnum.HOST_AUTO))
        assert_that(host.auto_manage_type, equal_to(HostManageEnum.VMWARE))
        assert_that(host.health, instance_of(UnityHealth))
        assert_that(host.name, equal_to('10.244.209.90'))
        assert_that(host.description, equal_to(''))
        assert_that(host.os_type, equal_to('VMware ESXi 6.0.0'))
        assert_that(host.host_pushed_uuid,
                    equal_to('5322a3d1-2901-08c3-c39f-f80f41fafe2e'))
        assert_that(host.host_polled_uuid,
                    equal_to('rfc4122.cd9f4de2-78a5-11e3-85bd-f80f41fafe2e'))
        assert_that(str(host.last_poll_time),
                    equal_to('2016-03-03 04:40:13+00:00'))
        assert_that(host.host_container, instance_of(UnityHostContainer))
        assert_that(host.iscsi_host_initiators,
                    instance_of(UnityHostInitiatorList))
        assert_that(host.host_ip_ports, instance_of(UnityHostIpPortList))
        assert_that(host.datastores, instance_of(UnityDataStoreList))
        assert_that(host.vms, instance_of(UnityVmList))

    @patch_rest
    def test_nested_properties(self):
        host = UnityHost(_id='Host_12', cli=t_rest())
        assert_that(
            host.fc_host_initiators.initiator_id,
            only_contains('20:00:00:00:C9:F3:AB:0C:10:00:00:00:C9:F3:AB:0C',
                          '20:00:00:00:C9:F3:AB:0D:10:00:00:00:C9:F3:AB:0D'))
        assert_that(host.iscsi_host_initiators.initiator_id, only_contains(
            'iqn.1998-01.com.vmware:esx239209-7e7a57a4'))
        assert_that(host.fc_host_initiators[0].paths[0].is_logged_in,
                    equal_to(True))
        assert_that(
            host.fc_host_initiators[1].paths[0].fc_port.wwn,
            equal_to('50:06:01:60:C7:E0:01:DA:50:06:01:6C:47:E0:01:DA'))

    @patch_rest
    def test_properties_in_tenant(self):
        host = UnityHost(_id='Host_16', cli=t_rest())
        assert_that(host.id, equal_to('Host_16'))
        assert_that(host.tenant, instance_of(UnityTenant))
        assert_that(host.tenant.id, equal_to('tenant_1'))
        assert_that(host.tenant.vlans, only_contains(1, 3))

    @patch_rest
    def test_get_all(self):
        hosts = UnityHostList(cli=t_rest())
        assert_that(len(hosts), equal_to(7))

    @patch_rest
    def test_get_host_ip_with_mask(self):
        host = UnityHost.get_host(t_rest(), '10.244.209.90/32')
        assert_that(host.ip_list, only_contains('10.244.209.90'))

    @patch_rest
    def test_get_host_in_tenant_with_ip(self):
        host = UnityHost.get_host(t_rest(), '192.168.112.23',
                                  tenant='tenant_1')
        assert_that(host.tenant.id, equal_to('tenant_1'))
        host = UnityHost.get_host(t_rest(), '192.168.112.23')
        assert_that(host.tenant, equal_to(None))

    @patch_rest
    def test_get_host_in_tenant_when_tenant_not_supported(self):
        def do():
            UnityHost.get_host(t_rest('3.1.0'), '192.168.112.23',
                               tenant='tenant_1')
        assert_that(do, raises(SystemAPINotSupported))

    @patch_rest
    def test_get_host_with_force_create(self):
        host = UnityHost.get_host(t_rest(), '192.168.112.24',
                                  tenant='tenant_1',
                                  force_create=True)
        assert_that(host._id, equal_to('Host_15'))

    @ddt.data({'version': '3.3.0'},
              {'version': '4.0.1'})
    @ddt.unpack
    @patch_rest
    def test_get_host_with_ip(self, version):
        host = UnityHost.get_host(t_rest(version), '10.244.209.90')
        assert_that(host.ip_list, only_contains('10.244.209.90'))

    @patch_rest
    def test_ip_list_of_host_list(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_31')
        assert_that(share.read_write_hosts.ip_list, only_contains('1.1.1.1'))
        assert_that(share.read_only_hosts.ip_list, equal_to([]))
        assert_that(share.root_access_hosts, none())

    @patch_rest
    def test_create_simple_host(self):
        host = UnityHost.create(t_rest(), name='host1',
                                host_type=HostTypeEnum.HOST_MANUAL,
                                os='customized os')
        assert_that(host.get_id(), equal_to('Host_11'))
        assert_that(host.name, equal_to('host1'))
        assert_that(host.os_type, equal_to('customized os'))

    @patch_rest
    def test_delete_host_success(self):
        host = UnityHost(cli=t_rest(), _id='Host_11')
        resp = host.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_add_ip_port(self):
        host = UnityHost(cli=t_rest(), _id='Host_9')
        port = host.add_ip_port('1.1.1.1')
        assert_that(port.existed, equal_to(True))
        assert_that(port.address, equal_to('1.1.1.1'))

    @patch_rest
    def test_delete_ip_port(self):
        host = UnityHost(cli=t_rest(), _id='Host_9')
        resp = host.delete_ip_port('1.1.1.1')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_host_and_ip_port(self):
        host = UnityHost(cli=t_rest(), _id='Host_1')
        ip_port = host.host_ip_ports[0]
        resp = host.delete()
        assert_that(resp.is_ok(), equal_to(True))
        assert_that(ip_port.delete, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_create_subset_host(self):
        host = UnityHost.get_host(t_rest(), '7.7.7.7/8', force_create=True)
        assert_that(host.ip_list, only_contains('7.7.7.7'))
        assert_that(host.type, equal_to(HostTypeEnum.SUBNET))

    @patch_rest
    def test_add_initiator(self):
        host = UnityHost(cli=t_rest(), _id='Host_9')
        wwn = "50:00:14:40:47:B0:0C:44:50:00:14:42:D0:0C:44:10"
        initiator = host.add_initiator(wwn)
        assert_that(initiator, instance_of(UnityHostInitiator))
        assert_that(initiator.existed, equal_to(True))
        assert_that(host.fc_host_initiators,
                    instance_of(UnityHostInitiatorList))

    @patch_rest
    def test_add_initiator_iscsi(self):
        host = UnityHost(cli=t_rest(), _id='Host_1')
        iqn = "iqn.1993-08.org.debian:01:a4f95ed19999"
        initiator = host.add_initiator(iqn)
        assert_that(initiator, instance_of(UnityHostInitiator))
        assert_that(initiator.existed, equal_to(True))
        assert_that(host.iscsi_host_initiators,
                    instance_of(UnityHostInitiatorList))

    @patch_rest
    def test_add_not_exist_initiator_with_force(self):
        host = UnityHost(cli=t_rest(), _id='Host_9')
        wwn = "50:00:14:40:47:B0:0C:44:50:00:14:42:D0:0C:99:99"
        initiator = host.add_initiator(wwn, force_create=True)
        assert_that(initiator, instance_of(UnityHostInitiator))
        assert_that(initiator.existed, equal_to(True))
        assert_that(host.fc_host_initiators,
                    instance_of(UnityHostInitiatorList))

    @patch_rest
    def test_add_initiator_not_exist(self):
        host = UnityHost(cli=t_rest(), _id='Host_9')
        wwn = "50:00:14:40:47:B0:0C:44:50:00:14:42:D0:0C:99:99"

        def f():
            host.add_initiator(wwn, force_create=False)

        assert_that(f, raises(UnityHostInitiatorNotFoundError))

    @patch_rest
    def test_delete_initiator(self):
        host = UnityHost(cli=t_rest(), _id='Host_1')
        wwn = "50:00:14:40:47:B0:0C:44:50:00:14:42:D0:0C:44:10"
        resp = host.delete_initiator(wwn)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_initiator_not_found(self):
        host = UnityHost(cli=t_rest(), _id='Host_1')
        wwn = "50:00:14:40:47:B0:0C:44:50:00:14:42:99:99:99:99"

        def f():
            host.delete_initiator(wwn)

        assert_that(f, raises(UnityHostInitiatorNotFoundError))

    @patch_rest
    def test_host_lun(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        assert_that(host.host_luns, instance_of(UnityHostLunList))
        assert_that(len(host.host_luns), equal_to(2))

    @patch_rest
    def test_get_all_host_lun_all(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        all_luns = host._get_host_lun()
        assert_that(len(all_luns), equal_to(2))

    @patch_rest
    def test_get_one_host_lun(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun1 = UnityLun(cli=t_rest(), _id="sv_2")
        which = host._get_host_lun(lun1)
        assert_that(len(which), equal_to(1))
        assert_that(which[0].lun.id, equal_to(lun1.id))

    @patch_rest
    def test_has_alu_true(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun1 = UnityLun(cli=t_rest(), _id="sv_2")
        has = host.has_alu(lun1)
        assert_that(has, equal_to(True))

    @patch_rest
    def test_has_alu_false(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun2 = UnityLun(cli=t_rest(), _id="sv_4")
        has = host.has_alu(lun2)
        assert_that(has, equal_to(False))

    @patch_rest
    def test_get_hlu(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun = UnityLun(cli=t_rest(), _id="sv_2")
        # UnityResourceList will return the found UnityResource
        # When '_id' as filter.
        host_lun = UnityHostLunList.get(cli=t_rest(), _id="Host_10_sv_2_prod")
        assert_that(host_lun, instance_of(UnityHostLun))
        hlu = host.get_hlu(lun)
        assert_that(hlu, equal_to(host_lun.hlu))

        # Be caureful, this will return UnityResourceList when 'id' as filter
        host_lun2 = UnityHostLunList.get(cli=t_rest(), id="Host_10_sv_2_prod")
        assert_that(host_lun2, instance_of(UnityHostLunList))
        assert_that(len(host_lun2), equal_to(1))
        assert_that(host_lun, equal_to(host_lun2[0]))

    @patch_rest
    def test_get_hlu_using_object_id_filter(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun = UnityLun(cli=t_rest(), _id="sv_2")
        filters = {'host.id': host.id, 'lun.id': lun.id}
        host_lun = UnityHostLunList.get(cli=t_rest(), **filters)
        assert_that(host_lun, instance_of(UnityHostLunList))
        assert_that(len(host_lun), equal_to(1))
        hlu = host.get_hlu(lun)
        assert_that(hlu, equal_to(host_lun[0].hlu))

    @patch_rest
    def test_get_hlu_not_found(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun = UnityLun(cli=t_rest(), _id="sv_4")
        hlu = host.get_hlu(lun)
        assert_that(hlu, equal_to(None))

    @patch_rest
    def test_detach_alu_without_host_access(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun = UnityLun(cli=t_rest(), _id="sv_2")
        resp = host.detach_alu(lun)
        assert_that(resp, equal_to(None))

    @patch_rest
    def test_detach_attached_hlu(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun = UnityLun(cli=t_rest(), _id="sv_2")
        resp = host.detach_alu(lun)
        assert_that(resp, equal_to(None))

    @patch_rest
    def test_detach_alu(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun = UnityLun(cli=t_rest(), _id="sv_4")
        resp = host.detach_alu(lun)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_attach_attached_hlu(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun = UnityLun(cli=t_rest(), _id="sv_2")

        def f():
            host.attach_alu(lun)

        assert_that(f, raises(UnityAluAlreadyAttachedError))

    @patch_rest
    def test_attach_alu(self):
        host = UnityHost(cli=t_rest(), _id='Host_10')
        lun = UnityLun(cli=t_rest(), _id="sv_4")
        hlu = host.attach_alu(lun)
        assert_that(hlu, equal_to(None))

    @patch_rest
    def test_attach_alu_exceed_limit(self):
        host = UnityHost(cli=t_rest(), _id='Host_11')
        lun = UnityLun(cli=t_rest(), _id="sv_2")

        def f():
            host.attach_alu(lun)

        assert_that(f, raises(UnityAttachAluExceedLimitError))

    @patch_rest
    def test_attach_snap_skip_first_hlu(self):
        def f():
            host = UnityHost(cli=t_rest(), _id='Host_11')
            snap = UnitySnap(_id='38654705676', cli=t_rest())
            host.attach(snap, skip_hlu_0=True)

        assert_that(f, raises(UnitySnapAlreadyPromotedException))

    @patch_rest
    def test_get_attached_cg_snap_hlu(self):
        host = UnityHost(cli=t_rest(), _id='Host_22')
        snap = UnitySnap(cli=t_rest(), _id='85899345930')
        lun = UnityLun(cli=t_rest(), _id='sv_3338')
        assert_that(host.get_hlu(snap, lun), equal_to(2))

    @patch_rest
    def test_get_hlu_of_cg_member(self):
        host = UnityHost(cli=t_rest(), _id='Host_22')
        lun = UnityLun(cli=t_rest(), _id='sv_3338')
        assert_that(host.get_hlu(lun), equal_to(3))


class UnityHostIpPortTest(TestCase):
    @patch_rest
    def test_properties(self):
        ip_port = UnityHostIpPort(cli=t_rest(), _id='HostNetworkAddress_1')
        assert_that(ip_port.host, instance_of(UnityHost))
        assert_that(ip_port.address, equal_to('10.244.209.90'))
        assert_that(ip_port.type, equal_to(HostPortTypeEnum.IPv4))

    @patch_rest
    def test_get_all(self):
        ip_ports = UnityHostIpPortList(cli=t_rest())
        assert_that(len(ip_ports), equal_to(8))

    @patch_rest
    def test_create_success(self):
        ip_port = UnityHostIpPort.create(t_rest(), 'Host_9', '1.1.1.1')
        assert_that(ip_port.address, equal_to('1.1.1.1'))
        assert_that(ip_port.type, equal_to(HostPortTypeEnum.IPv4))
        assert_that(ip_port.existed, equal_to(True))

    @patch_rest
    def test_create_ip_in_use(self):
        def f():
            UnityHostIpPort.create(t_rest(), 'Host_1', '1.1.1.1')

        assert_that(f, raises(UnityHostIpInUseError, 'already exists'))

    @patch_rest
    def test_delete_success(self):
        ip_port = UnityHostIpPort(cli=t_rest(), _id='HostNetworkAddress_10')
        resp = ip_port.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_get_by_ip(self):
        ip_ports = UnityHostIpPortList(cli=t_rest(), address='10.244.209.90')
        assert_that(len(ip_ports), equal_to(1))
        assert_that(ip_ports[0].address, equal_to('10.244.209.90'))


class UnityHostInitiatorTest(TestCase):
    @patch_rest
    def test_fc_initiator_properties(self):
        initiator = UnityHostInitiator(cli=t_rest(), _id='HostInitiator_2')
        assert_that(initiator, instance_of(UnityHostInitiator))
        assert_that(initiator.existed, equal_to(True))
        assert_that(initiator.health, instance_of(UnityHealth))
        assert_that(initiator.health.value, equal_to(HealthEnum.OK))
        assert_that(initiator.type, equal_to(HostInitiatorTypeEnum.FC))
        wwn = "50:00:14:40:47:B0:0C:44:50:00:14:42:D0:0C:44:10"
        assert_that(initiator.initiator_id, equal_to(wwn))
        assert_that(initiator.parent_host, instance_of(UnityHost))
        assert_that(initiator.is_ignored, equal_to(False))
        assert_that(initiator.is_chap_secret_enabled, equal_to(False))
        assert_that(initiator.node_wwn, equal_to("50:00:14:40:47:B0:0C:44"))
        assert_that(initiator.port_wwn, equal_to("50:00:14:42:D0:0C:44:10"))
        assert_that(initiator.paths, instance_of(UnityHostInitiatorPathList))
        assert_that(initiator.source_type,
                    equal_to(HostInitiatorSourceTypeEnum.OPEN_NATIVE))

    @patch_rest
    def test_iscsi_initiator_properties(self):
        initiator = UnityHostInitiator(cli=t_rest(), _id='HostInitiator_3')
        assert_that(initiator, instance_of(UnityHostInitiator))
        assert_that(initiator.existed, equal_to(True))
        assert_that(initiator.health, instance_of(UnityHealth))
        assert_that(initiator.health.value, equal_to(HealthEnum.OK))
        assert_that(initiator.type, equal_to(HostInitiatorTypeEnum.ISCSI))
        iqn = "iqn.1993-08.org.debian:01:a4f95ed14d65"
        assert_that(initiator.initiator_id, equal_to(iqn))
        assert_that(initiator.parent_host, instance_of(UnityHost))
        assert_that(initiator.is_ignored, equal_to(False))
        assert_that(initiator.is_chap_secret_enabled, equal_to(True))
        assert_that(initiator.paths, instance_of(UnityHostInitiatorPathList))
        assert_that(initiator.chap_user_name, equal_to(iqn))
        assert_that(initiator.iscsi_type,
                    equal_to(HostInitiatorIscsiTypeEnum.SOFTWARE))
        assert_that(initiator.is_bound, equal_to(False))
        assert_that(initiator.source_type,
                    equal_to(HostInitiatorSourceTypeEnum.DELL))

    @patch_rest
    def test_fc_initiator_create(self):
        host = UnityHost(cli=t_rest(), _id='Host_9')
        type = HostInitiatorTypeEnum.FC
        wwn = "50:00:14:40:47:B0:0C:44:50:00:14:42:D0:0C:44:10"
        initiator = UnityHostInitiator.create(t_rest(), wwn, host, type)
        assert_that(initiator, instance_of(UnityHostInitiator))
        assert_that(initiator.initiator_id, equal_to(wwn))

    @patch_rest
    def test_iscsi_initiator_create(self):
        host = UnityHost(cli=t_rest(), _id='Host_9')
        type = HostInitiatorTypeEnum.ISCSI
        iqn = "iqn.1993-08.org.debian:01:a4f95ed14d65"
        initiator = UnityHostInitiator.create(t_rest(), iqn, host, type)
        assert_that(initiator, instance_of(UnityHostInitiator))
        assert_that(initiator.initiator_id, equal_to(iqn))

    @patch_rest
    def test_unknown_initiator_create(self):
        host = UnityHost(cli=t_rest(), _id='Host_9')
        type = HostInitiatorTypeEnum.UNKNOWN
        iqn = "iqn.1993-08.org.debian:01:a4f95ed14d65"

        def f():
            UnityHostInitiator.create(t_rest(), iqn, host, type)

        assert_that(f, raises(UnityHostInitiatorUnknownType))

    @patch_rest
    def test_initiator_modify(self):
        initiator = UnityHostInitiator(cli=t_rest(), _id='HostInitiator_2')
        assert_that(initiator.parent_host, instance_of(UnityHost))
        assert_that(initiator.parent_host.id, equal_to("Host_1"))
        host = UnityHost(cli=t_rest(), _id='Host_19')
        resp = initiator.modify(host=host)
        assert_that(resp.is_ok(), equal_to(True))
        assert_that(initiator.parent_host, instance_of(UnityHost))

    @patch_rest
    def test_initiator_delete(self):
        initiator = UnityHostInitiator(cli=t_rest(), _id='HostInitiator_2')
        resp = initiator.delete()
        assert_that(resp.is_ok(), equal_to(True))


class UnityHostInitiatorPathListTest(TestCase):
    @patch_rest
    def test_filter(self):
        is_logged_in = True

        all_paths = UnityHostInitiatorPathList(cli=t_rest())
        paths = all_paths.shadow_copy(is_logged_in=is_logged_in)
        assert_that(len(paths), equal_to(2))
        assert_that(all(p.is_logged_in for p in paths), equal_to(True))

        paths = UnityHostInitiatorPathList(cli=t_rest(),
                                           is_logged_in=is_logged_in)
        assert_that(len(paths), equal_to(2))
        assert_that(all(p.is_logged_in for p in paths), equal_to(True))
