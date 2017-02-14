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

from hamcrest import assert_that, greater_than_or_equal_to, \
    raises, contains_string
from hamcrest import equal_to

from storops_test.vnx.nas_mock import t_nas, patch_post
from storops.exception import VNXBackendError
from storops.vnx.resource.cifs_server import VNXCifsServer, CifsDomain

__author__ = 'Jay Xu'


class VNXCifsServerTest(unittest.TestCase):
    # todo: test modify

    @patch_post
    def test_get_all(self):
        cifs_list = VNXCifsServer.get(t_nas())
        assert_that(len(cifs_list), greater_than_or_equal_to(1))
        cifs = next(cifs for cifs in cifs_list if cifs.name == 'CIFS')
        self.verify_pie_cifs(cifs)

    @patch_post
    def test_get_all_by_mover(self):
        cifs_list = VNXCifsServer.get(t_nas(), mover_id=1)
        cifs = next(cifs for cifs in cifs_list if cifs.name == 'CIFS')
        self.verify_pie_cifs(cifs)

    @patch_post
    def test_get_all_by_mover_not_found(self):
        cifs_list = VNXCifsServer.get(t_nas(), mover_id=1, is_vdm=True)
        assert_that(len(cifs_list), equal_to(0))

    @patch_post
    def test_get_by_name(self):
        cifs = VNXCifsServer.get(t_nas(), 'CIFS')
        self.verify_pie_cifs(cifs)

    @patch_post
    def test_get_by_name_not_found(self):
        cifs = VNXCifsServer('not_found', t_nas())
        assert_that(cifs.existed, equal_to(False))
        assert_that(cifs._get_name(), equal_to('not_found'))

    def verify_pie_cifs(self, cifs):
        assert_that(cifs.mover_id, equal_to(1))
        assert_that(cifs.existed, equal_to(True))
        assert_that(cifs.name, equal_to('CIFS'))
        assert_that(cifs.interfaces, equal_to('10.110.24.194'))
        assert_that(cifs.is_vdm, equal_to(False))
        assert_that(cifs.workgroup, equal_to('PIE'))
        assert_that(cifs.local_users, equal_to(True))
        assert_that(cifs.type, equal_to('standalone'))

    @patch_post
    def test_create_cifs_server_invalid_domain_name(self):
        try:
            domain = CifsDomain('test_domain')
            VNXCifsServer.create(t_nas(), 'test', 1, domain=domain)
            self.fail('should raise an exception.')
        except VNXBackendError as ex:
            assert_that(ex.message, contains_string('not facet-valid'))

    @patch_post
    def test_create_cifs_server_no_default_nt_server(self):
        def f():
            domain = CifsDomain('test.dev')
            VNXCifsServer.create(t_nas(), 'test', 1, domain=domain)

        assert_that(f, raises(VNXBackendError, 'default NT server'))

    @patch_post
    def test_create_cifs_server_net_bios_existed(self):
        def f():
            domain = CifsDomain('test.dev')
            VNXCifsServer.create(t_nas(), 'test', 1,
                                 domain=domain,
                                 interfaces='10.110.24.194')

        assert_that(f, raises(VNXBackendError, 'already exists as server'))

    @patch_post
    def test_create_cifs_server_w2k(self):
        domain = CifsDomain('test.dev')
        cifs = VNXCifsServer.create(t_nas(), 's8', 1, domain=domain,
                                    interfaces='10.110.24.194')
        assert_that(cifs.domain, equal_to('TEST.DEV'))
        assert_that(cifs.type, equal_to('W2K'))
        assert_that(cifs.comp_name, equal_to('S8'))
        assert_that(cifs.domain_joined, equal_to(False))

    @patch_post
    def test_delete_cifs_server(self):
        cifs = VNXCifsServer('test', t_nas())
        resp = cifs.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_post
    def test_delete_cifs_server_not_found(self):
        def f():
            cifs = VNXCifsServer('test1', t_nas())
            cifs.delete(1)

        assert_that(f, raises(VNXBackendError, 'does not exist'))

    @patch_post
    def test_create_cifs_server_stand_alone(self):
        cifs = VNXCifsServer.create(t_nas(), 's2', 1, workgroup='work',
                                    interfaces='10.110.24.194',
                                    local_admin_password='password')
        assert_that(cifs.workgroup, equal_to('WORK'))
        assert_that(cifs.name, equal_to('S2'))

    @patch_post
    def test_create_cifs_default_mover(self):
        cifs = VNXCifsServer.create(t_nas(), 's2', workgroup='work',
                                    interfaces='10.110.24.194',
                                    local_admin_password='password')
        assert_that(cifs.existed, equal_to(True))
        assert_that(cifs.workgroup, equal_to('WORK'))
        assert_that(cifs.name, equal_to('S2'))
