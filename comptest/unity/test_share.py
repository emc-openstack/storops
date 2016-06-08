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
from hamcrest import assert_that, equal_to, has_items, has_item, none

from comptest.utils import is_jenkins
from storops import HostTypeEnum, ACEAccessLevelEnum

__author__ = 'Cedric Zhuang'


def test_check_cifs_share_exists(unity_gf):
    assert_that(unity_gf.cifs_share.existed, equal_to(True))


def test_create_delete_cifs_share_snapshot(unity_gf):
    # create snap
    snap = unity_gf.cifs_share.create_snap(unity_gf.add_snap_name())
    assert_that(unity_gf.cifs_share.storage_resource.id,
                equal_to(snap.storage_resource.id))

    # delete snap
    resp = snap.delete()
    snap.update()
    assert_that(resp.is_ok(), equal_to(True))
    assert_that(snap.existed, equal_to(False))


def test_check_nfs_share_exists(unity_gf):
    assert_that(unity_gf.nfs_share.existed, equal_to(True))


def test_create_delete_nfs_share_snapshot(unity_gf):
    # create snap
    snap = unity_gf.nfs_share.create_snap(unity_gf.add_snap_name())
    assert_that(unity_gf.nfs_share.storage_resource.id,
                equal_to(snap.storage_resource.id))

    # delete snap
    resp = snap.delete()
    snap.update()
    assert_that(resp.is_ok(), equal_to(True))
    assert_that(snap.existed, equal_to(False))


def test_create_snap_based_nfs_share_and_snap(unity_gf):
    snap = unity_gf.nfs_share.create_snap(unity_gf.add_snap_name())

    # create snap based share
    nfs_share = snap.create_nfs_share(name=snap.name)
    assert_that(nfs_share.existed, equal_to(True))

    # create snap of snap based share
    share_snap = nfs_share.create_snap(unity_gf.add_snap_name())
    assert_that(share_snap.existed, equal_to(True))


def test_create_snap_based_cifs_share_and_snap(unity_gf):
    snap = unity_gf.cifs_share.create_snap(unity_gf.add_snap_name())

    # create snap based share
    cifs_share = snap.create_cifs_share(name=snap.name)
    assert_that(cifs_share.existed, equal_to(True))

    # create snap of snap based share
    share_snap = cifs_share.create_snap(unity_gf.add_snap_name())
    assert_that(share_snap.existed, equal_to(True))


def test_nfs_share_read_write_host_access(unity_gf):
    share = unity_gf.create_nfs_share()
    share.allow_read_write_access(['1.1.1.1', '1.1.1.2'],
                                  force_create_host=True)

    share.update()
    assert_that(share.read_write_hosts.ip_list,
                has_items('1.1.1.1', '1.1.1.2'))

    share.deny_access(['1.1.1.1', '1.1.1.2'])
    share.update()
    assert_that(share.no_access_hosts.ip_list, has_items('1.1.1.1', '1.1.1.2'))


def test_nfs_share_mixed_host_access(unity_gf):
    share = unity_gf.nfs_share
    share.allow_read_only_access('1.1.1.3', force_create_host=True)
    share.allow_root_access('1.1.1.4', force_create_host=True)
    share.update()
    assert_that(share.read_only_hosts.ip_list, has_item('1.1.1.3'))
    assert_that(share.root_access_hosts.ip_list, has_item('1.1.1.4'))

    share.deny_access(['1.1.1.3', '1.1.1.4'])
    share.update()
    assert_that(share.read_only_hosts, none())
    assert_that(share.root_access_hosts, none())
    assert_that(share.no_access_hosts.ip_list, has_items('1.1.1.3', '1.1.1.4'))


def test_deny_access_to_subnet(unity_gf):
    share = unity_gf.nfs_share
    share.deny_access('7.7.7.7/8', force_create_host=True)

    share.update()
    assert_that(share.no_access_hosts.ip_list, has_items('7.7.7.7'))

    host = unity_gf.unity.get_host(address='7.7.7.7')
    assert_that(host.type, equal_to(HostTypeEnum.SUBNET))


@pytest.mark.skipif(is_jenkins(), reason='No run on CI, manual only.')
def test_cifs_access_control(unity_cs):
    share = unity_cs.cifs_share
    resp = share.enable_ace()
    assert_that(resp.is_ok(), equal_to(True))

    access_list = share.get_ace_list()
    orig = len(access_list[ACEAccessLevelEnum.FULL])

    share.add_ace('win2012.dev', 'SMIS_User_1')
    access_list = share.get_ace_list()
    assert_that(len(access_list[ACEAccessLevelEnum.FULL]), equal_to(orig + 1))

    share.delete_ace('win2012.dev', 'SMIS_User_1')
    access_list = share.get_ace_list()
    assert_that(len(access_list[ACEAccessLevelEnum.FULL]), equal_to(orig))

    resp = share.disable_ace()
    assert_that(resp.is_ok(), equal_to(True))
