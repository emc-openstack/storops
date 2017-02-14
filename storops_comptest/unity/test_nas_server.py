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

import pytest
from hamcrest import assert_that, equal_to, only_contains

from storops import FileInterfaceRoleEnum

__author__ = 'Cedric Zhuang'


def test_check_nas_server_create_success(unity_gf):
    assert_that(unity_gf.nas_server.existed, equal_to(True))


def test_check_cifs_server_create_success(unity_gf):
    assert_that(unity_gf.nas_server.get_cifs_server().existed, equal_to(True))


def test_check_nfs_server_create_success(unity_gf):
    nfs_servers = unity_gf.unity.get_nfs_server()
    for nfs_server in nfs_servers:
        nas_server = nfs_server.nas_server
        if nas_server and nas_server.id == unity_gf.nas_server.id:
            break
    else:
        pytest.fail('cannot find the nfs server for nas server: {}'
                    .format(unity_gf.nas_server))


def test_create_delete_file_interface(unity_gf):
    ip = '2.2.2.2'
    fi = unity_gf.nas_server.create_file_interface(
        'spb_eth2', ip, role=FileInterfaceRoleEnum.PRODUCTION)
    assert_that(fi.existed, equal_to(True))
    assert_that(fi.ip_address, equal_to(ip))
    fi.delete()


def test_create_delete_dns_server(unity_gf):
    ip = '1.1.1.1'
    fi = unity_gf.nas_server.create_file_interface(
        'spa_eth2', ip, role=FileInterfaceRoleEnum.PRODUCTION)
    dns = unity_gf.nas_server.create_dns_server('test.dev', ip)
    assert_that(dns.existed, equal_to(True))
    assert_that(dns.addresses, only_contains(ip))
    dns.delete()
    fi.delete()
