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

from hamcrest import assert_that, equal_to, has_item, raises, instance_of, \
    none, is_not, has_items, only_contains, close_to, greater_than, not_none

from storops.exception import VNXStorageGroupError, \
    VNXStorageGroupNameInUseError, VNXDetachAluNotFoundError, \
    VNXAluAlreadyAttachedError, VNXAluNotFoundError, VNXHluNumberInUseError, \
    VNXHluAlreadyUsedError
from storops.lib.common import cache
from storops.vnx.enums import VNXSPEnum
from storops.vnx.resource.lun import VNXLun
from storops.vnx.resource.port import VNXStorageGroupHBAList
from storops.vnx.resource.sg import VNXStorageGroupList, VNXStorageGroup
from test.vnx.cli_mock import patch_cli, t_cli
from test.vnx.resource.test_lun import get_lun_list

__author__ = 'Cedric Zhuang'


@patch_cli
@cache
def get_sg_list():
    return VNXStorageGroupList(t_cli())


class VNXStorageGroupListTest(TestCase):
    sg_list = get_sg_list()

    @patch_cli
    def test_get_sg_list(self):
        assert_that(self.sg_list.name,
                    has_items('VNX9495', 'ubuntu-server11', 'ubuntu-server7',
                              'ubuntu14'))
        assert_that(len(self.sg_list), equal_to(4))

    @patch_cli
    def test_poll_property(self):
        sg = self.sg_list.get('ubuntu14')
        sg.poll = False
        lun_list = sg.lun_list
        lun = lun_list[0]
        assert_that(lun_list.poll, equal_to(False))
        assert_that(lun.poll, equal_to(False))

    @patch_cli
    def test_detach_not_existed_lun(self):
        lun = VNXLun(name='y', cli=t_cli())
        # raise no error
        self.sg_list.detach_alu(lun)

    @patch_cli
    def test_get_sg_by_name(self):
        sg = self.sg_list.get('ubuntu14')
        assert_that(sg.name, equal_to('ubuntu14'))

    @patch_cli
    def test_system_lun_list_supplied(self):
        lun_list = get_lun_list()
        sgs = VNXStorageGroup.get(t_cli(), system_lun_list=lun_list)
        assert_that(len(sgs), equal_to(4))
        assert_that(lun_list.timestamp, not_none())
        for sg in sgs:
            assert_that(sg.lun_list.timestamp, equal_to(lun_list.timestamp))


def get_sg(name='server7'):
    sg = VNXStorageGroup(name=name, cli=t_cli())
    sg.shuffle_hlu = False
    return sg


class VNXStorageGroupTest(TestCase):
    sg_7 = get_sg()

    @patch_cli
    def test_properties(self):
        sg = self.sg_7
        assert_that(sg.name, equal_to('server7'))
        assert_that(
            sg.wwn,
            equal_to('F6:F1:04:29:91:97:E5:11:85:E1:AE:04:FD:64:DC:17'))
        assert_that(sg.shareable, equal_to(True))
        assert_that(len(sg.alu_hlu_map), greater_than(1))
        assert_that(sg.alu_hlu_map[10], equal_to(153))
        assert_that(len(sg.hba_sp_pairs), equal_to(15))
        assert_that(sg.uid, equal_to(sg.wwn))
        assert_that(sg.has_alu(10), equal_to(True))
        assert_that(sg.has_alu(11), equal_to(False))
        assert_that(sg.has_hlu(153), equal_to(True))
        assert_that(sg.has_hlu(11), equal_to(False))
        assert_that(sg.existed, equal_to(True))

    @patch_cli
    def test_property_hosts(self):
        hosts = get_sg('~management').hosts
        assert_that(len(hosts), equal_to(2))
        assert_that(hosts.name,
                    has_items('APM00152312055-spB', 'APM00152312055-spA'))
        assert_that(hosts[0].storage_group.name, equal_to('~management'))

    @patch_cli
    def test_property_lun_list(self):
        sg = get_sg('microsoft')
        sg.poll = False
        lun_list = sg.lun_list
        assert_that(lun_list.name, only_contains('lun4', 'lun456'))
        assert_that(lun_list.poll, equal_to(False))

    @patch_cli
    def test_property_zero_lun_list(self):
        lun_list = get_sg('os01').lun_list
        assert_that(len(lun_list), equal_to(0))

    @patch_cli
    def test_get_sg_os01(self):
        sg = VNXStorageGroup(name='os01', cli=t_cli())
        assert_that(len(sg.hba_sp_pairs), equal_to(1))
        assert_that(sg.hba_sp_pairs, instance_of(VNXStorageGroupHBAList))
        hba = sg.hba_sp_pairs[0]
        assert_that(hba.sp, equal_to(VNXSPEnum.SP_A))
        assert_that(hba.uid,
                    equal_to('iqn.1993-08.org.debian:01:95bbe389e025'))
        assert_that(hba.port_id, equal_to(4))

    @patch_cli
    def test_initiator_uid_list(self):
        sg = get_sg('microsoft')
        assert_that(len(sg.initiator_uid_list), equal_to(2))
        assert_that(sg.initiator_uid_list,
                    has_item('iqn.1991-05.com.microsoft:abc.def.dev'))

    @patch_cli
    def test_hba_ports(self):
        sg = self.sg_7
        assert_that(len(sg.hba_port_list), equal_to(15))
        assert_that(len(sg.ports), equal_to(8))
        assert_that(len(sg.initiator_uid_list), equal_to(5))

    @patch_cli
    def test_iscsi_ports_all(self):
        assert_that(len(self.sg_7.iscsi_ports), equal_to(1))

    @patch_cli
    def test_fc_ports_all(self):
        assert_that(len(self.sg_7.fc_ports), equal_to(7))

    @patch_cli
    def test_get_fc_ports_with_filter_found_one(self):
        ports = self.sg_7.get_fc_ports(sp=VNXSPEnum.SP_A, port_id=2)
        assert_that(len(ports), equal_to(1))
        port = ports[0]
        assert_that(port.sp, equal_to(VNXSPEnum.SP_A))
        assert_that(port.port_id, equal_to(2))

    @patch_cli
    def test_get_iscsi_ports_with_filter_type_not_match(self):
        ports = self.sg_7.get_iscsi_ports(sp=VNXSPEnum.SP_A, port_id=2)
        assert_that(len(ports), equal_to(0))

    @patch_cli
    def test_get_port_by_sp(self):
        sg = self.sg_7
        assert_that(len(sg.get_ports(sp=VNXSPEnum.SP_A)), equal_to(5))
        assert_that(len(sg.get_ports(sp=VNXSPEnum.SP_B)), equal_to(3))
        assert_that(len(sg.get_ports(sp=VNXSPEnum.SP_A, port_id=0)),
                    equal_to(1))
        assert_that(len(sg.get_ports(sp=VNXSPEnum.SP_A, port_id=9)),
                    equal_to(0))

    @patch_cli
    def test_get_ports_by_wwn(self):
        wwn = '20:00:00:90:FA:53:4C:D0:10:00:00:90:FA:53:4C:D0'
        ports = self.sg_7.get_ports(wwn)
        assert_that(len(ports), equal_to(6))
        for port in ports:
            assert_that(port.host_initiator_list, has_item(wwn))

    @patch_cli
    def test_get_ports_no_wwn(self):
        ports = self.sg_7.get_ports()
        assert_that(len(ports), equal_to(8))

    @patch_cli
    def test_attach_alu_success(self):
        sg = self.sg_7
        lun = VNXLun(name='x', cli=t_cli())
        assert_that(sg.has_alu(0), equal_to(False))
        hlu = sg.attach_alu(lun)
        assert_that(sg.has_alu(0), equal_to(True))
        assert_that(sg.get_hlu(0), equal_to(1))
        assert_that(hlu, equal_to(1))

    @patch_cli
    def test_attach_alu_already_attached(self):
        sg = self.sg_7

        def f():
            sg.attach_alu(123)

        assert_that(f, raises(VNXAluAlreadyAttachedError,
                              'already been added'))
        assert_that(sg.get_hlu(123), none())
        assert_that(len(sg.get_alu_hlu_map()), equal_to(2))

    @patch_cli
    def test_attach_alu_hlu_used(self):
        sg = self.sg_7

        def f():
            sg.attach_alu(123, hlu=210)

        assert_that(f, VNXHluAlreadyUsedError, 'already used')

    @patch_cli
    def test_attach_with_hlu_alu_not_found(self):
        sg = self.sg_7

        def f():
            sg.attach_alu(123, hlu=212)

        assert_that(f, VNXAluNotFoundError, 'not a bound ALU number')

    @patch_cli
    def test_attach_alu_with_hlu_success(self):
        sg = get_sg()
        hlu_id = sg.attach_alu(2, hlu=1)
        assert_that(hlu_id, equal_to(1))
        assert_that(sg.has_alu(2), equal_to(True))
        assert_that(sg.has_hlu(1), equal_to(True))

    @patch_cli
    def test_attach_alu_not_found(self):
        sg = self.sg_7

        def f():
            sg.attach_alu(124)

        assert_that(f, raises(VNXAluNotFoundError,
                              'not a bound ALU number'))
        assert_that(sg.get_hlu(124), none())
        assert_that(len(sg.get_alu_hlu_map()), equal_to(2))

    @patch_cli
    def test_attach_alu_already_attached_found_in_cache(self):
        sg = self.sg_7
        assert_that(sg.get_hlu(10), equal_to(153))
        assert_that(len(sg.get_alu_hlu_map()), equal_to(2))
        try:
            sg.attach_alu(10)
            self.fail('should have raised exception.')
        except VNXAluAlreadyAttachedError:
            assert_that(sg.get_hlu(10), equal_to(153))
            assert_that(len(sg.get_alu_hlu_map()), equal_to(2))

    @patch_cli
    def test_attach_alu_hlu_in_use_retry(self):
        def f():
            sg = self.sg_7
            sg.attach_alu(13, retry_limit=2)

        assert_that(f, raises(VNXHluNumberInUseError,
                              'LUN Number already in use'))

    @patch_cli
    def test_detach_hlu_success(self):
        sg = get_sg()
        sg.detach_alu(10)
        assert_that(sg.has_hlu(10), equal_to(False))

    @patch_cli
    def test_detach_hlu_not_found(self):
        def f():
            sg = self.sg_7
            sg.detach_alu(1032)

        assert_that(f, raises(VNXDetachAluNotFoundError, 'No such Host LUN'))

    @patch_cli
    def test_detach_hlu_not_attached(self):
        def f():
            sg = self.sg_7
            sg.detach_alu(1033)

        assert_that(f, raises(VNXDetachAluNotFoundError,
                              'is not attached'))

    @patch_cli
    def test_connect_host(self):
        def f():
            sg = self.sg_7
            sg.connect_host('host1')

        assert_that(f, raises(VNXStorageGroupError,
                              'Host specified is not known'))

    @patch_cli
    def test_disconnect_host(self):
        def f():
            sg = self.sg_7
            sg.disconnect_host('host1')

        assert_that(f, raises(VNXStorageGroupError,
                              'not currently connected'))

    @patch_cli
    def test_create_sg_name_in_use(self):
        def f():
            VNXStorageGroup.create('existed', t_cli())

        assert_that(f, raises(VNXStorageGroupNameInUseError, 'already in use'))

    @patch_cli
    def test_empty_sg_property(self):
        sg = VNXStorageGroup.get(t_cli(), 'sg1')
        wwn = 'BB:50:E8:2F:23:01:E6:11:83:36:00:60:16:58:B3:E9'
        assert_that(sg.name, equal_to('sg1'))
        assert_that(sg.wwn, equal_to(wwn))
        assert_that(len(sg.initiator_uid_list), equal_to(0))
        assert_that(len(sg.ports), equal_to(0))
        assert_that(len(sg.fc_ports), equal_to(0))
        assert_that(len(sg.iscsi_ports), equal_to(0))
        assert_that(len(sg.hba_sp_pairs), equal_to(0))

    @patch_cli
    def test_get_hlu_to_add_no_shuffle(self):
        sg = get_sg()
        sg.shuffle_hlu = False
        assert_that(sg._get_hlu_to_add(12), equal_to(1))
        sg._delete_alu(12)
        assert_that(len(sg.get_alu_hlu_map()), equal_to(2))
        assert_that(sg._get_hlu_to_add(12), equal_to(1))
        sg._delete_alu(12)
        assert_that(len(sg.get_alu_hlu_map()), equal_to(2))

    @patch_cli
    def test_get_hlu_to_add_shuffle(self):
        sg = VNXStorageGroup.get(t_cli(), 'server7')
        first = sg._get_hlu_to_add(12)
        sg._delete_alu(12)
        assert_that(len(sg.get_alu_hlu_map()), equal_to(2))
        second = sg._get_hlu_to_add(12)
        assert_that(first, is_not(equal_to(second)))
        sg._delete_alu(12)
        assert_that(len(sg.get_alu_hlu_map()), equal_to(2))

    @patch_cli
    def test_lun_list_from_shadow_copy(self):
        lun_list = get_lun_list()
        sg = VNXStorageGroup.get(cli=t_cli(), name='sg1',
                                 system_lun_list=lun_list)
        assert_that(len(sg.lun_list), equal_to(2))
        assert_that(sg.lun_list.timestamp, equal_to(lun_list.timestamp))

    sg = VNXStorageGroup.get(t_cli(), 'sg1')

    @patch_cli
    def test_sg_read_iops(self):
        assert_that(self.sg.read_iops, equal_to(3.5))

    @patch_cli
    def test_sg_write_iops(self):
        assert_that(self.sg.write_iops, equal_to(9.0))

    @patch_cli
    def test_sg_total_iops(self):
        assert_that(self.sg.total_iops, equal_to(12.5))

    @patch_cli
    def test_sg_read_mbps(self):
        assert_that(self.sg.read_mbps, equal_to(2.3 + 4.6))

    @patch_cli
    def test_sg_write_mbps(self):
        assert_that(self.sg.write_mbps, equal_to(2.7 + 5.4))

    @patch_cli
    def test_sg_total_mbps(self):
        assert_that(self.sg.total_mbps, equal_to(5.0 + 10.0))

    @patch_cli
    def test_sg_read_size_kb(self):
        assert_that(self.sg.read_size_kb, close_to(2018, 1))

    @patch_cli
    def test_sg_write_size_kb(self):
        assert_that(self.sg.write_size_kb, close_to(921, 1))
