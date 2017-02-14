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

from hamcrest import assert_that, greater_than_or_equal_to, raises
from hamcrest import equal_to

from storops_test.vnx.nas_mock import t_nas, patch_nas
from storops.vnx.enums import VNXShareType
from storops.exception import VNXBackendError, VNXInvalidMoverID, \
    VNXMoverInterfaceNotAttachedError, VNXMoverInterfaceNotExistsError
from storops.vnx.resource.vdm import VNXVdm

__author__ = 'Jay Xu'


class VNXVdmTest(unittest.TestCase):
    @patch_nas
    def test_get_all(self):
        vdm_list = VNXVdm.get(t_nas())
        assert_that(len(vdm_list), greater_than_or_equal_to(1))
        dm = next(dm for dm in vdm_list if dm.vdm_id == 2)
        self.verify_vdm_2(dm)

    @patch_nas
    def test_get_by_id_invalid(self):
        dm = VNXVdm.get(vdm_id=1, cli=t_nas())
        assert_that(dm.existed, equal_to(False))

    @patch_nas
    def test_get_by_id_2(self):
        dm = VNXVdm(vdm_id=2, cli=t_nas())
        self.verify_vdm_2(dm)

    @patch_nas
    def test_get_by_name(self):
        dm = VNXVdm.get(name='VDM_ESA', cli=t_nas())
        self.verify_vdm_2(dm)

    @patch_nas
    def test_get_by_name_not_found(self):
        dm = VNXVdm(name='not_found', cli=t_nas())
        assert_that(dm.existed, equal_to(False))

    @staticmethod
    def verify_vdm_2(dm):
        assert_that(dm.root_fs_id, equal_to(199))
        assert_that(dm.mover_id, equal_to(1))
        assert_that(dm.name, equal_to('VDM_ESA'))
        assert_that(dm.existed, equal_to(True))
        assert_that(dm.vdm_id, equal_to(2))
        assert_that(dm.state, equal_to('loaded'))
        assert_that(dm.status, equal_to('ok'))
        assert_that(dm.is_vdm, equal_to(True))

    @patch_nas
    def test_create_vdm_invalid_mover_id(self):
        def f():
            VNXVdm.create(t_nas(), 3, 'myVdm')

        assert_that(f, raises(VNXInvalidMoverID))

    @patch_nas
    def test_create_vdm(self):
        dm = VNXVdm.create(t_nas(), 2, 'myVdm')
        assert_that(dm.name, equal_to('myVdm'))
        assert_that(dm.vdm_id, equal_to(3))
        assert_that(dm.mover_id, equal_to(2))
        assert_that(dm.root_fs_id, equal_to(245))

    @patch_nas
    def test_delete_vdm(self):
        dm = VNXVdm(vdm_id=3, cli=t_nas())
        resp = dm.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_nas
    def test_delete_vdm_not_found(self):
        def f():
            dm = VNXVdm(vdm_id=5, cli=t_nas())
            dm.delete()

        assert_that(f, raises(VNXBackendError, 'not found'))

    @patch_nas
    def test_attach_interface_success(self):
        dm = VNXVdm(name='myvdm', cli=t_nas())
        dm.attach_nfs_interface('1.1.1.1-0')

    @patch_nas
    def test_attach_interface_not_found(self):
        def f():
            dm = VNXVdm(name='myvdm', cli=t_nas())
            dm.attach_nfs_interface('1.1.1.2-0')

        assert_that(f, raises(VNXMoverInterfaceNotExistsError, 'not exist'))

    @patch_nas
    def test_detach_interface_success(self):
        dm = VNXVdm(name='myvdm', cli=t_nas())
        dm.detach_nfs_interface('1.1.1.1-0')

    @patch_nas
    def test_detach_interface_not_found(self):
        def f():
            dm = VNXVdm(name='myvdm', cli=t_nas())
            dm.detach_nfs_interface('1.1.1.2-0')

        assert_that(f, raises(VNXMoverInterfaceNotExistsError, 'not exist'))

    @patch_nas
    def test_detach_interface_not_attached(self):
        def f():
            dm = VNXVdm(name='myvdm', cli=t_nas())
            dm.detach_nfs_interface('1.1.1.3-0')

        assert_that(f, raises(VNXMoverInterfaceNotAttachedError, 'attached'))

    @patch_nas
    def test_get_interfaces(self):
        dm = VNXVdm(name='VDM_ESA', cli=t_nas())
        ifs = dm.get_interfaces()
        assert_that(len(ifs), equal_to(1))
        interface = ifs[0]
        assert_that(interface.name, equal_to('10-110-24-195'))
        assert_that(interface.share_type, equal_to(VNXShareType.NFS))
