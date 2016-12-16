# coding=utf-8
# Copyright (c) 2016 EMC Corporation.
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

from hamcrest import assert_that, only_contains, instance_of, raises
from hamcrest import equal_to
from storops.unity.resource.tenant import UnityTenant, UnityTenantList
from storops.unity.resource.host import UnityHostList
from storops.unity.resource.nas_server import UnityNasServerList
from storops.exception import UnityTenantNameInUseError, SystemAPINotSupported
from test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Tina Tang'


class UnityTenantTest(TestCase):
    @patch_rest()
    def test_create_tenant(self):
        UnityTenant.create(t_rest('4.1.0'), 'test',
                           uuid='173ca6c3-5952-427d-82a6-df88f49e3926',
                           vlans=[3])

    @patch_rest()
    def test_create_tenant_unsupported(self):
        def f():
            UnityTenant.create(t_rest('4.0.0'), 'test',
                               uuid='173ca6c3-5952-427d-82a6-df88f49e3926',
                               vlans=[3])
        assert_that(f, raises(SystemAPINotSupported))

    @patch_rest()
    def test_create_tenant_failed_name_inused(self):
        def do():
            UnityTenant.create(t_rest('4.1.0'), 'dup',
                               vlans=[3])

        assert_that(do, raises(UnityTenantNameInUseError,
                               'The specified tenant name is already in use'))

    @patch_rest()
    def test_tenant_modify_vlans(self):
        tenant = UnityTenant('tenant_1', cli=t_rest('4.1.0'))
        tenant.modify(vlans=[4])

    @patch_rest()
    def test_tenant_modify_name(self):
        tenant = UnityTenant('tenant_1', cli=t_rest('4.1.0'))
        tenant.modify(name='new_name')

    @patch_rest()
    def test_properties(self):
        tenant = UnityTenant('tenant_1', cli=t_rest('4.1.0'))
        assert_that(tenant.name, equal_to('T1'))
        assert_that(tenant.uuid,
                    equal_to('173ca6c3-5952-427d-82a6-df88f49e3926'))
        assert_that(tenant.vlans, instance_of(list))
        assert_that(tenant.vlans, only_contains(1, 3))
        assert_that(len(tenant.hosts), equal_to(1))
        assert_that(tenant.hosts, instance_of(UnityHostList))
        assert_that(tenant.nas_servers, instance_of(UnityNasServerList))
        assert_that(len(tenant.nas_servers), equal_to(1))

    @patch_rest()
    def test_get_all(self):
        tenants = UnityTenantList(cli=t_rest('4.1.0'))
        assert_that(len(tenants), equal_to(3))

    @patch_rest()
    def test_query_tenant_with_vlans(self):
        tenants = UnityTenantList(cli=t_rest('4.1.0'),
                                  vlans=[1, 3])
        assert_that(len(tenants), equal_to(1))

    @patch_rest()
    def test_delete_tenant(self):
        tenant = UnityTenant('tenant_1', cli=t_rest())
        tenant.delete()

    @patch_rest()
    def test_delete_tenant_with_hosts(self):
        tenant = UnityTenant('tenant_2', cli=t_rest())
        tenant.delete(delete_hosts=True)
