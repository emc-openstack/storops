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

from unittest import TestCase

from hamcrest import assert_that, raises, equal_to, has_item, none, is_not, \
    only_contains, contains_string

from storops.exception import VNXInvalidCliParamError, \
    VNXPortNotInitializedError, VNXInitiatorExistedError, \
    VNXDeleteHbaNotFoundError, VNXPingNodeTimeOutError, VNXGateWayError, \
    VNXVirtualPortNotFoundError
from storops.lib.common import instance_cache
from storops.vnx.enums import VNXSPEnum, VNXPortType
from storops.vnx.resource.port import VNXHbaPort, VNXSPPort, \
    VNXConnectionPort, VNXStorageGroupHBA
from storops.vnx.resource.sg import VNXStorageGroup
from test.vnx.cli_mock import patch_cli, t_cli
from test.vnx.resource.fakes import STORAGE_GROUP_HBA

__author__ = 'Cedric Zhuang'


class VNXSPPortTest(TestCase):
    @patch_cli
    def test_port_list(self):
        ports = VNXSPPort.get(t_cli())
        assert_that(len(ports), equal_to(32))

    @patch_cli
    def test_port_get_sp(self):
        ports = VNXSPPort.get(t_cli(), VNXSPEnum.SP_B)
        assert_that(len(ports), equal_to(16))

    @patch_cli
    def test_port_get_id(self):
        ports = VNXSPPort.get(t_cli(), port_id=5)
        assert_that(len(ports), equal_to(2))

    @patch_cli
    def test_index_sequence(self):
        # this test will fail if the index is not used as splitter is wrong
        ports = VNXSPPort.get(t_cli(), VNXSPEnum.SP_A, 15)
        assert_that(ports[0].wwn, equal_to(
            '50:06:01:60:B6:E0:16:81:50:06:01:67:36:E4:16:81'))

    @patch_cli
    def test_get_port_property(self):
        port = VNXSPPort.get(t_cli(), VNXSPEnum.SP_A, 0)[0]
        assert_that(port.sp, equal_to(VNXSPEnum.SP_A))
        assert_that(port.port_id, equal_to(0))
        assert_that(port.vport_id, none())
        assert_that(port.index, equal_to('A_0'))
        assert_that(port.wwn, equal_to(
            '50:06:01:60:B6:E0:16:81:50:06:01:60:36:E0:16:81'))
        assert_that(port.link_status, equal_to('Up'))
        assert_that(port.port_status, equal_to('Online'))
        assert_that(port.switch_present, equal_to(True))
        assert_that(port.speed_value, equal_to('8Gbps'))
        assert_that(port.registered_initiators, equal_to(3))
        assert_that(port.logged_in_initiators, equal_to(1))
        assert_that(port.not_logged_in_initiators, equal_to(2))
        assert_that(port.type, equal_to(VNXPortType.FC))
        assert_that(port.display_name, equal_to('A-0'))
        assert_that(port.sfp_state, equal_to('Online'))
        assert_that(port.reads, equal_to(1))
        assert_that(port.writes, equal_to(2))
        assert_that(port.blocks_read, equal_to(3))
        assert_that(port.blocks_written, equal_to(4))
        assert_that(port.queue_full_busy, equal_to(5))
        assert_that(port.i_o_module_slot, equal_to('6'))
        assert_that(port.physical_port_id, equal_to(7))
        assert_that(port.usage, equal_to("General"))
        assert_that(port.sfp_connector_emc_part_number,
                    equal_to('019-078-042'))
        assert_that(port.sfp_connector_emc_serial_number,
                    equal_to('000000000000000'))
        assert_that(port.sfp_connector_vendor_part_number, equal_to('N/A'))
        assert_that(port.sfp_connector_vendor_serial_number,
                    equal_to('PL31D5E'))

    @patch_cli
    def test_get_port_by_type(self):
        ports = VNXSPPort.get(cli=t_cli(), port_type=VNXPortType.ISCSI)
        assert_that(len(ports), equal_to(4))
        ports = VNXSPPort.get(cli=t_cli(), port_type=VNXPortType.FC)
        assert_that(len(ports), equal_to(28))

    @property
    @instance_cache
    def port_a0(self):
        return VNXSPPort.get(t_cli(), sp=VNXSPEnum.SP_A, port_id=0)[0]

    @patch_cli
    def test_port_read_iops(self):
        assert_that(self.port_a0.read_iops, equal_to(10.0))

    @patch_cli
    def test_port_write_iops(self):
        assert_that(self.port_a0.write_iops, equal_to(20.0))

    @patch_cli
    def test_port_total_iops(self):
        assert_that(self.port_a0.total_iops, equal_to(30.0))

    @patch_cli
    def test_port_read_mbps(self):
        assert_that(self.port_a0.read_mbps, equal_to(1.0))

    @patch_cli
    def test_port_write_mbps(self):
        assert_that(self.port_a0.write_mbps, equal_to(1.5))

    @patch_cli
    def test_port_total_mbps(self):
        assert_that(self.port_a0.total_mbps, equal_to(2.5))

    @patch_cli
    def test_port_read_size_kb(self):
        assert_that(self.port_a0.read_size_kb, equal_to(102.4))

    @patch_cli
    def test_port_write_size_kb(self):
        assert_that(self.port_a0.write_size_kb, equal_to(76.8))

    @patch_cli
    def test_property_names(self):
        assert_that(self.port_a0.property_names(), has_item('read_iops'))


class VNXHbaPortTest(TestCase):
    def test_from_storage_group_hba(self):
        hba = VNXStorageGroupHBA.parse(STORAGE_GROUP_HBA)
        port = VNXHbaPort.from_storage_group_hba(hba)
        assert_that(port.sp, equal_to(VNXSPEnum.SP_A))
        assert_that(port.port_id, equal_to(3))
        assert_that(port.vport_id, equal_to(1))
        assert_that(port.type, equal_to(VNXPortType.ISCSI))
        assert_that(port.host_initiator_list,
                    has_item('iqn.1991-05.com.microsoft:abc.def.dev'))

    def test_hash(self):
        ports = {
            VNXHbaPort.create(VNXSPEnum.SP_A, 1),
            VNXHbaPort.create(VNXSPEnum.SP_B, 1),
            VNXHbaPort.create(VNXSPEnum.SP_A, 1)
        }
        assert_that(len(ports), equal_to(2))

    def test_set_sp(self):
        port = VNXHbaPort.create('A', 3)
        assert_that(port.sp, equal_to(VNXSPEnum.SP_A))

    def test_set_sp_error(self):
        port = VNXHbaPort.create('Z', 3)
        assert_that(port.is_valid(), equal_to(False))
        assert_that(port.sp, none())

    def test_set_number_error(self):
        def f():
            port = VNXHbaPort.create('A', 'a1')
            assert_that(port.is_valid(), equal_to(False))
            assert_that(port.port_id, none())

        assert_that(f, raises(ValueError, 'must be an integer.'))

    def test_create_tuple_input(self):
        inputs = ('a', 5)
        port = VNXHbaPort.create(*inputs)
        assert_that(port.sp, equal_to(VNXSPEnum.SP_A))
        assert_that(port.port_id, equal_to(5))

    def test_get_sp_index(self):
        port = VNXHbaPort.create('spb', '5')
        assert_that(port.get_sp_index(), equal_to('b'))
        assert_that(port.port_id, equal_to(5))

    def test_equal(self):
        spa_1 = VNXHbaPort.create(VNXSPEnum.SP_A, 1)
        spa_1_dup = VNXHbaPort.create(VNXSPEnum.SP_A, 1)
        spa_2 = VNXHbaPort.create(VNXSPEnum.SP_A, 2)
        assert_that(spa_1_dup, equal_to(spa_1))
        assert_that(spa_1, is_not(equal_to(spa_2)))

    def test_as_tuple(self):
        port = VNXHbaPort.create(VNXSPEnum.SP_A, 1)
        assert_that(port.as_tuple(), only_contains(VNXSPEnum.SP_A, 1))

    def test_repr(self):
        port = VNXHbaPort.create(VNXSPEnum.SP_B, 3)
        ret = port.__repr__()
        assert_that(ret, contains_string('"sp": "VNXSPEnum.SP_B"'))
        assert_that(ret, contains_string('"existed": true'))


class VNXConnectionPortTest(TestCase):
    def test_port(self):
        return VNXConnectionPort(sp='a', port_id=4, cli=t_cli())

    @patch_cli
    def test_properties(self):
        port = self.test_port()
        assert_that(port.sp, equal_to(VNXSPEnum.SP_A))
        assert_that(port.port_id, equal_to(4))
        assert_that(port.wwn,
                    equal_to('iqn.1992-04.com.emc:cx.apm00153906536.a4'))
        assert_that(port.iscsi_alias, equal_to('6536.a4'))
        assert_that(port.enode_mac_address, equal_to('00-60-16-45-5D-FC'))
        assert_that(port.virtual_port_id, equal_to(0))
        assert_that(port.vport_id, equal_to(0))
        assert_that(port.vlan_id, none())
        assert_that(port.current_mtu, equal_to(1500))
        assert_that(port.auto_negotiate, equal_to(False))
        assert_that(port.port_speed, equal_to('10000 Mb'))
        assert_that(port.host_window, equal_to('256K'))
        assert_that(port.replication_window, equal_to('256K'))
        assert_that(port.ip_address, equal_to('192.168.4.52'))
        assert_that(port.subnet_mask, equal_to('255.255.255.0'))
        assert_that(port.gateway_address, equal_to('0.0.0.0'))
        assert_that(port.type, equal_to(VNXPortType.ISCSI))
        assert_that(port.existed, equal_to(True))
        assert_that(port.display_name, equal_to('A-4-0'))

    @patch_cli
    def test_get_all(self):
        ports = VNXConnectionPort.get(t_cli())
        assert_that(len(ports), equal_to(20))

    @patch_cli
    def test_get_by_sp(self):
        ports = VNXConnectionPort.get(t_cli(), VNXSPEnum.SP_A)
        assert_that(len(ports), equal_to(10))

    @patch_cli
    def test_get_by_port(self):
        ports = VNXConnectionPort.get(t_cli(), port_id=8)
        assert_that(len(ports), equal_to(2))

    @patch_cli
    def test_get_by_type(self):
        ports = VNXConnectionPort.get(t_cli(), port_type=VNXPortType.ISCSI)
        assert_that(len(ports), equal_to(16))
        ports = VNXConnectionPort.get(t_cli(), port_type=VNXPortType.FCOE)
        assert_that(len(ports), equal_to(4))

    @patch_cli
    def test_get_single(self):
        ports = VNXConnectionPort.get(t_cli(), VNXSPEnum.SP_A, 4)
        assert_that(len(ports), equal_to(1))
        port = ports[0]
        assert_that(port.port_id, equal_to(4))
        assert_that(port.sp, equal_to(VNXSPEnum.SP_A))

    @patch_cli
    def test_get_port_not_found(self):
        ports = VNXConnectionPort.get(t_cli(), VNXSPEnum.SP_A, 44)
        assert_that(len(ports), equal_to(0))

    @patch_cli
    def test_get_port_with_vport_not_found(self):
        port = VNXConnectionPort.get(t_cli(), VNXSPEnum.SP_B, 10, 0)
        assert_that(port.existed, equal_to(False))

    @patch_cli
    def test_delete_fc_hba_success(self):
        uid = '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00'
        # no error raised
        VNXSPPort.delete_hba(t_cli(), uid)

    @patch_cli
    def test_delete_hba_already_removed(self):
        def f():
            uid = '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:01'
            VNXSPPort.delete_hba(t_cli(), uid)

        assert_that(f, raises(VNXDeleteHbaNotFoundError))

    @patch_cli
    def test_ping_node_timeout(self):
        def f():
            port = VNXConnectionPort.get(t_cli(), VNXSPEnum.SP_A, 8)[0]
            port.ping_node('10.244.211.3', count=1)

        assert_that(f, raises(VNXPingNodeTimeOutError))

    @patch_cli
    def test_ping_node_success(self):
        port = VNXConnectionPort.get(t_cli(), VNXSPEnum.SP_A, 8)[0]
        # success, no error raised
        port.ping_node('10.244.211.4', count=1)

    @patch_cli
    def test_ping_node_multiple_success(self):
        port = VNXConnectionPort.get(t_cli(), VNXSPEnum.SP_A, 8)[0]
        # success, no error raised
        port.ping_node('10.244.211.5')

    @patch_cli
    def test_config_ip_gateway_error(self):
        def f():
            port = VNXConnectionPort.get(t_cli(), VNXSPEnum.SP_A, 10)[0]
            port.config_ip('6.6.6.6', '255.255.255.0', '5.5.5.1')

        assert_that(f, raises(VNXGateWayError, 'netmask'))

    @patch_cli
    def test_delete_ip_not_found(self):
        def f():
            port = VNXConnectionPort.get(t_cli(), VNXSPEnum.SP_A, 10)[0]
            port.delete_ip()

        assert_that(f, raises(VNXVirtualPortNotFoundError, 'not found'))


def test_hba():
    return VNXStorageGroupHBA().update(STORAGE_GROUP_HBA)


class VNXStorageGroupHBATest(TestCase):
    def test_properties(self):
        hba = test_hba()
        assert_that(hba.host_name, equal_to('abc.def.dev'))
        assert_that(hba.initiator_ip, equal_to('10.244.209.72'))
        assert_that(hba.sp_port, equal_to('A-3v1'))

    def test_sp(self):
        assert_that(test_hba().sp, equal_to(VNXSPEnum.SP_A))

    def test_uid(self):
        assert_that(test_hba().uid,
                    equal_to('iqn.1991-05.com.microsoft:abc.def.dev'))

    def test_port_id(self):
        assert_that(test_hba().port_id, equal_to(3))

    def test_vlan(self):
        assert_that(test_hba().vlan, equal_to(1))

    def test_port_type(self):
        assert_that(test_hba().port_type,
                    equal_to(VNXPortType.ISCSI))

    @patch_cli
    def test_set_path_with_sp_port_invalid_wwn(self):
        def f():
            ports = VNXSPPort.get(sp=VNXSPEnum.SP_A, port_id=0, cli=t_cli())
            sg = VNXStorageGroup(cli=t_cli(), name='sg0')
            sg.set_path(ports[0], '11:22:33', 'host0')

        assert_that(f, raises(VNXInvalidCliParamError))

    @patch_cli
    def test_set_path_with_fc_port_success(self):
        wwn = '01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F:10'
        ports = VNXSPPort.get(sp=VNXSPEnum.SP_A, port_id=0, cli=t_cli())
        sg = VNXStorageGroup(cli=t_cli(), name='sg0')
        # no exception
        sg.set_path(ports[0], wwn, 'host0')

    @patch_cli
    def test_set_path_with_iscsi_port_not_initialized(self):
        def f():
            uid = 'iqn.1992-04.com.abc:a.b.c'
            port = VNXConnectionPort.get(sp=VNXSPEnum.SP_A, port_id=10,
                                         cli=t_cli())[0]
            sg = VNXStorageGroup(cli=t_cli(), name='sg0')
            sg.set_path(port, uid, 'host0')

        assert_that(f, raises(VNXPortNotInitializedError))

    @patch_cli
    def test_set_path_with_fcoe_port_success(self):
        uid = 'iqn.1992-04.com.abc:a.b.c'
        port = VNXConnectionPort.get(sp=VNXSPEnum.SP_A, port_id=8,
                                     vport_id=0, cli=t_cli())
        sg = VNXStorageGroup(cli=t_cli(), name='sg0')
        # no error raised
        sg.connect_hba(port, uid, 'host0')

    @patch_cli
    def test_set_path_with_fcoe_already_existed(self):
        def f():
            uid = 'iqn.1992-04.com.abc:a.b.d'
            port = VNXConnectionPort.get(sp=VNXSPEnum.SP_A, port_id=8,
                                         vport_id=0, cli=t_cli())
            sg = VNXStorageGroup(cli=t_cli(), name='sg0')
            sg.set_path(port, uid, 'host0')

        assert_that(f, raises(VNXInitiatorExistedError))


class VNXPortTest(TestCase):
    def hba_port_set(self):
        return {
            VNXHbaPort.create(VNXSPEnum.SP_A, 1),
            VNXHbaPort.create(VNXSPEnum.SP_B, 1),
            VNXHbaPort.create(VNXSPEnum.SP_A, 4),
            VNXHbaPort.create(VNXSPEnum.SP_A, 3, vport_id=1),
            VNXHbaPort.create(VNXSPEnum.SP_A, 6, vport_id=0),
            VNXHbaPort.create(VNXSPEnum.SP_B, 4, vport_id=0),
        }

    @patch_cli
    def test_connection_port_not_equal_sp_port(self):
        c_port = VNXConnectionPort(sp='a', port_id=4, cli=t_cli())
        s_port = VNXSPPort.get(t_cli(), VNXSPEnum.SP_A, 4)
        # one has vport_id, others not, not equal
        assert_that(c_port, is_not(equal_to(s_port)))

    @patch_cli
    def test_connection_port_equal_sp_port(self):
        c_port = VNXConnectionPort(sp='a', port_id=9, cli=t_cli())
        s_port = VNXSPPort.get(t_cli(), VNXSPEnum.SP_A, 9)[0]
        assert_that(c_port, equal_to(s_port))

    @patch_cli
    def test_connection_port_equal_hba_port(self):
        c_port = VNXConnectionPort(sp='a', port_id=4, cli=t_cli())
        h_port = VNXHbaPort.create('a', 4, vport_id=0)
        assert_that(c_port, equal_to(h_port))

    @patch_cli
    def test_sp_port_in_hba_port_set(self):
        ports = self.hba_port_set()
        s_port = VNXSPPort.get(t_cli(), VNXSPEnum.SP_A, 4)[0]
        assert_that(ports, has_item(s_port))

    @patch_cli
    def test_connection_port_not_in_hba_port_set(self):
        ports = self.hba_port_set()
        c_port = VNXConnectionPort(sp='a', port_id=4, cli=t_cli())
        assert_that(ports, is_not(has_item(c_port)))

        c_port = VNXConnectionPort(sp='a', port_id=9, cli=t_cli())
        assert_that(ports, is_not(has_item(c_port)))

    @patch_cli
    def test_connection_port_in_hba_port_set(self):
        ports = self.hba_port_set()
        c_port = VNXConnectionPort(sp='a', port_id=6, vport_id=0, cli=t_cli())
        assert_that(ports, has_item(c_port))

    @patch_cli
    def test_connection_port_in_sp_port_list(self):
        c_port = VNXConnectionPort(sp='a', port_id=9, cli=t_cli())
        ports = VNXSPPort.get(t_cli())
        assert_that(ports, has_item(c_port))

    @patch_cli
    def test_hba_equal_connection_port(self):
        hba = test_hba()
        c_port = VNXConnectionPort(sp='a', port_id=3, vport_id=1, cli=t_cli())
        assert_that(hba, equal_to(c_port))

    @patch_cli
    def test_hba_not_equal_sp_port(self):
        hba = test_hba()
        s_port = VNXSPPort.get(t_cli(), VNXSPEnum.SP_A, 3)
        assert_that(hba, is_not(equal_to(s_port)))

    @patch_cli
    def test_hba_in_sp_port(self):
        sg = VNXStorageGroup(name='server7', cli=t_cli())
        hba = None
        for hba in sg.ports:
            if hba.sp == VNXSPEnum.SP_A and hba.port_id == 0:
                break
        ports = VNXSPPort.get(t_cli())
        assert_that(ports, has_item(hba))

    @patch_cli
    def test_hba_in_hba_port(self):
        hba = test_hba()
        ports = self.hba_port_set()
        assert_that(ports, has_item(hba))

    @patch_cli
    def test_hba_equal_hba_port(self):
        hba = test_hba()
        h_port = VNXHbaPort.create('a', 3, vport_id=1)
        assert_that(hba, equal_to(h_port))

    @patch_cli
    def test_get_metrics_csv(self):
        ports = VNXSPPort.get(t_cli())
        csv = ports.get_metrics_csv()
        assert_that(csv, contains_string(',A_0,'))
        assert_that(csv, contains_string('30.0,2.5,'))
        assert_that(csv, contains_string('timestamp,name,'))
