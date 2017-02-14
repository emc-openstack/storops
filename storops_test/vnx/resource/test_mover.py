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
import unittest

from hamcrest import assert_that, equal_to, none, only_contains, raises

from storops_test.vnx.nas_mock import t_nas, patch_post, patch_nas
from storops.vnx.enums import VNXPortType
from storops.exception import VNXBackendError, VNXGeneralNasError
from storops.vnx.resource.mover import VNXMover, \
    VNXMoverRefList, VNXMoverRef, VNXMoverHost, VNXMoverHostList

__author__ = 'Jay Xu'


class VNXMoverRefTest(unittest.TestCase):
    @patch_post
    def test_get_all(self):
        movers = VNXMoverRefList(t_nas())
        assert_that(len(movers), equal_to(2))
        dm = next(dm for dm in movers if dm.mover_id == 1)
        self.verify_dm_ref_1(dm)

    @patch_post
    def test_get(self):
        dm = VNXMoverRef(mover_id=1, cli=t_nas())
        self.verify_dm_ref_1(dm)

    @patch_post
    def test_get_not_existed(self):
        dm = VNXMoverRef(mover_id=5, cli=t_nas())
        assert_that(dm.existed, equal_to(False))

    @patch_post
    def test_get_by_name(self):
        dm = VNXMoverRef(name='server_2', cli=t_nas())
        self.verify_dm_ref_1(dm)

    @patch_post
    def test_get_by_name_not_found(self):
        dm = VNXMoverRef(name='server_5', cli=t_nas())
        assert_that(dm.existed, equal_to(False))

    @staticmethod
    def verify_dm_ref_1(dm):
        assert_that(dm.mover_id, equal_to(1))
        assert_that(dm.i18n_mode, equal_to('UNICODE'))
        assert_that(dm.name, equal_to('server_2'))
        assert_that(dm.existed, equal_to(True))
        assert_that(dm.standby_fors, none())
        assert_that(dm.failover_policy, equal_to('auto'))
        assert_that(dm.host_id, equal_to(1))
        assert_that(dm.role, equal_to('primary'))
        assert_that(dm.standbys, only_contains(2))

    def test_get_id(self):
        dm = VNXMover(mover_id=12)
        assert_that(dm.get_id(dm), equal_to(12))
        assert_that(dm.get_id('22'), equal_to(22))

    @patch_post
    def test_mover_host(self):
        dm = VNXMover(mover_id=1, cli=t_nas())
        VNXMoverHostTest.verify_mover_host_1(dm.host)

    @patch_post
    def test_create_dns(self):
        dm = VNXMover.get(mover_id=1, cli=t_nas())
        resp = dm.create_dns('tt', '1.1.1.1')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_post
    def test_create_dns_format_error(self):
        def f():
            dm = VNXMover(mover_id=1, cli=t_nas())
            dm.create_dns('tt', '1.1.1.1,2.2.2.2')

        assert_that(f, raises(VNXBackendError, 'not facet-valid'))

    @patch_post
    def test_create_dns_multiple(self):
        dm = VNXMover(mover_id=1, cli=t_nas())
        resp = dm.create_dns('tt', ['1.1.1.1', '2.2.2.2'])
        assert_that(resp.is_ok(), equal_to(True))

    @patch_post
    def test_delete_dns(self):
        dm = VNXMoverRef(mover_id=1, cli=t_nas())
        resp = dm.delete_dns('tt')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_post
    def test_delete_dns_not_exist(self):
        def f():
            dm = VNXMoverRef(mover_id=1, cli=t_nas())
            dm.delete_dns('bb')

        assert_that(f, raises(VNXGeneralNasError, 'server_2'))

    @patch_post
    def test_physical_devices(self):
        dm = VNXMoverRef(mover_id=1, cli=t_nas())
        assert_that(len(dm.physical_devices), equal_to(9))

    @patch_post
    def test_fc_devices(self):
        dm = VNXMoverRef(mover_id=1, cli=t_nas())
        assert_that(len(dm.fc_devices), equal_to(4))

    @patch_post
    def test_ethernet_devices(self):
        dm = VNXMoverRef(mover_id=1, cli=t_nas())
        assert_that(len(dm.ethernet_devices), equal_to(4))

    @patch_post
    def test_create_interface(self):
        dm = VNXMover(mover_id=1, cli=t_nas())
        interface = dm.create_interface('cge-1-0', '1.1.1.1', '255.255.255.0')
        assert_that(interface.name, equal_to('1.1.1.1-0'))
        assert_that(interface.broadcast_addr, equal_to('1.1.1.255'))

    @patch_post
    def test_delete_interface(self):
        dm = VNXMover(mover_id=1, cli=t_nas())
        resp = dm.delete_interface('1.1.1.1')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_nas
    def test_get_interconnect_id(self):
        dm = VNXMover(mover_id=1, cli=t_nas())
        assert_that(dm.get_interconnect_id(), equal_to(20001))


class VNXMoverTest(unittest.TestCase):
    @patch_post
    def test_create_nfs_share(self):
        dm = VNXMover(mover_id=1, cli=t_nas())
        share = dm.create_nfs_share(path='/EEE')
        assert_that(share.path, equal_to('/EEE'))
        assert_that(share.mover_id, equal_to(1))
        assert_that(share.existed, equal_to(True))
        assert_that(share.fs_id, equal_to(243))

    @patch_post
    def test_get_all(self):
        movers = VNXMover.get(t_nas())
        assert_that(len(movers), equal_to(2))
        mover1 = next(dm for dm in movers if dm.mover_id == 1)
        self.verify_dm_1(mover1)

    @patch_post
    def test_get(self):
        mover1 = VNXMover.get(mover_id=1, cli=t_nas())
        self.verify_dm_1(mover1)

    @staticmethod
    def verify_dm_1(dm):
        assert_that(dm.status, equal_to('ok'))
        assert_that(dm.mover_id, equal_to(1))
        assert_that(dm.uptime, equal_to(7086723))
        assert_that(dm.i18n_mode, equal_to('UNICODE'))
        assert_that(dm.name, equal_to('server_2'))
        assert_that(dm.existed, equal_to(True))
        assert_that(dm.version, equal_to('T8.1.7.70'))
        assert_that(dm.standby_fors, none())
        assert_that(dm.dns_domain, none())
        assert_that(dm.failover_policy, equal_to('auto'))
        assert_that(dm.host_id, equal_to(1))
        assert_that(dm.role, equal_to('primary'))
        assert_that(dm.standbys, only_contains(2))
        assert_that(dm.timezone, equal_to('GMT'))
        interface = next(i for i in dm.interfaces if i.name == 'el30')
        assert_that(interface.mover_id, equal_to(1))
        assert_that(interface.ip_addr, equal_to('172.18.70.2'))
        assert_that(interface.name, equal_to('el30'))
        assert_that(interface.existed, equal_to(True))
        assert_that(interface.broadcast_addr, equal_to('172.18.255.255'))
        assert_that(interface.net_mask, equal_to('255.255.0.0'))
        assert_that(interface.up, equal_to(True))
        assert_that(interface.mtu, equal_to(1500))
        assert_that(interface.ip_version, equal_to('IPv4'))
        assert_that(interface.mac_addr, equal_to('2:60:48:20:b:0'))
        assert_that(interface.device, equal_to('cge0'))
        assert_that(interface.vlan_id, equal_to(0))
        dedup_settings = dm.dedup_settings
        assert_that(dedup_settings.cpu_high_watermark, equal_to(90))
        assert_that(dedup_settings.minimum_scan_interval, equal_to(7))
        assert_that(dedup_settings.duplicate_detection_method,
                    equal_to('sha1'))
        assert_that(dedup_settings.mover_id, equal_to(1))
        assert_that(dedup_settings.minimum_size, equal_to(24))
        assert_that(dedup_settings.access_time, equal_to(15))
        assert_that(dedup_settings.file_extension_exclude_list, equal_to(''))
        assert_that(dedup_settings.case_sensitive, equal_to(False))
        assert_that(dedup_settings.cifs_compression_enabled, equal_to(True))
        assert_that(dedup_settings.modification_time, equal_to(15))
        assert_that(dedup_settings.sav_vol_high_watermark, equal_to(90))
        assert_that(dedup_settings.backup_data_high_watermark, equal_to(90))
        assert_that(dedup_settings.maximum_size, equal_to(8388608))
        assert_that(dedup_settings.cpu_low_watermark, equal_to(40))
        assert_that(dedup_settings.existed, equal_to(True))
        device = next(i for i in dm.devices if i.name == 'fxg-8-0')
        assert_that(device.mover_id, equal_to(1))
        assert_that(device.name, equal_to('fxg-8-0'))
        assert_that(device.existed, equal_to(True))
        assert_that(device.type, equal_to('physical-ethernet'))
        assert_that(device.interfaces, equal_to('10.110.42.83'))
        assert_that(device.speed, equal_to('FD10000'))
        route = next(i for i in dm.route if i.destination == '172.18.0.0')
        assert_that(route.mover_id, equal_to(1))
        assert_that(route.existed, equal_to(True))
        assert_that(route.destination, equal_to('172.18.0.0'))
        assert_that(route.net_mask, equal_to('255.255.0.0'))
        assert_that(route.ip_version, equal_to('IPv4'))
        assert_that(route.interface, equal_to('172.18.70.2'))
        assert_that(route.gateway, equal_to('172.18.70.2'))


class VNXMoverHostTest(unittest.TestCase):
    @patch_post
    def test_get_by_id(self):
        mh = VNXMoverHost(host_id=1, cli=t_nas())
        self.verify_mover_host_1(mh)

    @patch_post
    def test_get_all(self):
        mh_list = VNXMoverHostList(t_nas())
        assert_that(len(mh_list), equal_to(2))
        mh = next(mh for mh in mh_list if mh.host_id == 1)
        self.verify_mover_host_1(mh)

    @patch_post
    def test_get_by_id_not_found(self):
        mh = VNXMoverHost(host_id=5, cli=t_nas())
        assert_that(mh.existed, equal_to(False))

    @classmethod
    def verify_mover_host_1(cls, mh):
        assert_that(mh.host_id, equal_to(1))
        assert_that(mh.slot, equal_to(2))
        assert_that(mh.existed, equal_to(True))
        assert_that(mh.mover_id, equal_to(1))
        assert_that(mh.status, equal_to('ok'))
        motherboard = mh.motherboard
        assert_that(motherboard.existed, equal_to(True))
        assert_that(motherboard.mover_host, equal_to(1))
        assert_that(motherboard.bus_speed, equal_to(4800))
        assert_that(motherboard.memory_size, equal_to(12288))
        assert_that(motherboard.cpu_type, equal_to('Intel Four Core Westmere'))
        assert_that(motherboard.cpu_speed, equal_to(2133))
        assert_that(motherboard.board_type, equal_to('CMB-Argonaut'))
        fcp02 = next(device for device in mh.physical_device
                     if device.name == 'fcp-0-2')
        cls.verify_fcp_02(fcp02)
        cge13 = next(device for device in mh.physical_device
                     if device.name == 'cge-1-3')
        cls.verify_cge13(cge13)

    @staticmethod
    def verify_cge13(cge13):
        assert_that(cge13.existed, equal_to(True))
        assert_that(cge13.name, equal_to('cge-1-3'))
        assert_that(cge13.irq, equal_to(27))
        assert_that(cge13.mover_host, equal_to(1))
        assert_that(cge13.port_number, equal_to(0))
        assert_that(cge13.allowed_speeds,
                    equal_to('FD1000 FD100 HD100 FD10 HD10 auto'))
        assert_that(cge13.port_wwn, none())
        assert_that(cge13.type, equal_to(VNXPortType.ETHERNET))
        assert_that(cge13.description, equal_to('Broadcom Gigabit'))
        assert_that(cge13.is_internal, equal_to(False))

    @staticmethod
    def verify_fcp_02(fcp02):
        assert_that(fcp02.existed, equal_to(True))
        assert_that(fcp02.name, equal_to('fcp-0-2'))
        assert_that(fcp02.irq, equal_to(22))
        assert_that(fcp02.mover_host, equal_to(1))
        assert_that(fcp02.port_number, equal_to(0))
        assert_that(fcp02.allowed_speeds, none())
        assert_that(fcp02.port_wwn, equal_to('50:06:01:62:47:60:44:06'))
        assert_that(fcp02.type, equal_to(VNXPortType.FC))
        assert_that(fcp02.description, equal_to('PMC QE8'))
        assert_that(fcp02.is_internal, equal_to(False))
