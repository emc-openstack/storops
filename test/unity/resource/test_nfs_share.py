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

from hamcrest import equal_to, assert_that, only_contains, instance_of, \
    raises, none
from storops.unity.resource.snap import UnitySnap

from storops.exception import UnityException, UnityNfsShareNameExistedError, \
    UnityHostNotFoundException, UnitySnapNameInUseError
from storops.unity.enums import NFSTypeEnum, NFSShareRoleEnum, \
    NFSShareDefaultAccessEnum, NFSShareSecurityEnum
from storops.unity.resource.filesystem import UnityFileSystem
from storops.unity.resource.host import UnityHostList, UnityHost
from storops.unity.resource.nfs_share import UnityNfsShare, \
    UnityNfsShareList, UnityNfsHostConfig
from test.unity.rest_mock import patch_rest, t_rest

__author__ = 'Cedric Zhuang'


def host(_id):
    return UnityHost(_id=_id, cli=t_rest())


class UnityNfsShareTest(TestCase):
    @patch_rest
    def test_properties(self):
        nfs = UnityNfsShare('NFSShare_1', cli=t_rest())
        assert_that(nfs.id, equal_to('NFSShare_1'))
        assert_that(nfs.type, equal_to(NFSTypeEnum.NFS_SHARE))
        assert_that(nfs.role, equal_to(NFSShareRoleEnum.PRODUCTION))
        assert_that(nfs.default_access,
                    equal_to(NFSShareDefaultAccessEnum.ROOT))
        assert_that(nfs.min_security, equal_to(NFSShareSecurityEnum.SYS))
        assert_that(nfs.name, equal_to('esa_nfs1'))
        assert_that(nfs.path, equal_to(r'/'))
        assert_that(nfs.export_paths,
                    only_contains(r'10.244.220.120:/esa_nfs1'))
        assert_that(nfs.description, equal_to('bcd'))
        assert_that(str(nfs.creation_time),
                    equal_to('2016-03-02 02:39:22.856000+00:00'))
        assert_that(str(nfs.modification_time),
                    equal_to('2016-03-02 02:39:22.856000+00:00'))
        assert_that(nfs.filesystem.get_id(), equal_to('fs_1'))
        assert_that(nfs.filesystem, instance_of(UnityFileSystem))
        assert_that(nfs.tenant, equal_to(None))

    @patch_rest
    def test_tenant_properties(self):
        nfs = UnityNfsShare('NFSShare_32', cli=t_rest())
        assert_that(nfs.tenant.id, equal_to('tenant_1'))

    @patch_rest
    def test_host_access_properties(self):
        nfs = UnityNfsShare('NFSShare_5', cli=t_rest())
        assert_that(nfs.read_write_hosts, only_contains(host('Host_7')))
        assert_that(nfs.read_only_hosts, none())
        assert_that(nfs.root_access_hosts, none())
        assert_that(nfs.no_access_hosts, none())

    @patch_rest
    def test_get_all(self):
        nfs_list = UnityNfsShareList(cli=t_rest())
        assert_that(len(nfs_list), equal_to(2))

    @patch_rest
    def test_create_nfs_share_fs_not_support(self):
        def f():
            UnityNfsShare.create(t_rest(), 'ns1', 'fs_8')

        assert_that(f, raises(UnityException, 'not support NFS'))

    @patch_rest
    def test_create_nfs_share_success(self):
        share = UnityNfsShare.create(
            t_rest(), 'ns1', 'fs_9',
            share_access=NFSShareDefaultAccessEnum.READ_WRITE)
        assert_that(share.name, equal_to('ns1'))
        assert_that(share.id, equal_to('NFSShare_4'))

    @patch_rest
    def test_create_nfs_share_name_exists(self):
        def f():
            UnityNfsShare.create(
                t_rest(), 'ns1', 'fs_9',
                share_access=NFSShareDefaultAccessEnum.ROOT)

        assert_that(f, raises(UnityNfsShareNameExistedError, 'already exists'))

    @patch_rest
    def test_delete_nfs_share_success(self):
        share = UnityNfsShare(_id='NFSShare_4', cli=t_rest())
        resp = share.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_nfs_share_snap_existed(self):
        def f():
            share = UnityNfsShare(_id='NFSShare_31', cli=t_rest())
            share.create_snap('share_snap')

        assert_that(f, raises(UnitySnapNameInUseError, 'in use'))

    @patch_rest
    def test_delete_nfs_share_async(self):
        share = UnityNfsShare(_id='NFSShare_6', cli=t_rest())
        resp = share.delete(async=True)
        job = resp.job
        assert_that(job.existed, equal_to(True))
        assert_that(str(job.est_remain_time), equal_to('0:00:01'))

    @patch_rest
    def test_delete_snap_based_share(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_11')
        resp = share.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_modify_read_write_hosts(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_5')
        resp = share.modify(read_write_hosts=['Host_7'])
        assert_that(resp.is_ok(), equal_to(True))
        share.update()
        assert_that(share.read_write_hosts, instance_of(UnityHostList))
        assert_that(share.read_write_hosts[0].get_id(), equal_to('Host_7'))

    @patch_rest
    def test_modify_multiple_hosts(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_5')
        host7 = UnityHost(_id='Host_7', cli=t_rest())
        resp = share.modify(read_only_hosts=host7,
                            read_write_hosts=['Host_1', 'Host_2'])
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_add_ip_access_force_create(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_5')
        h1 = UnityHost(_id='Host_1', cli=t_rest())
        resp = share.allow_read_write_access([h1, '1.1.1.2'],
                                             force_create_host=True)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_add_ip_access_existed(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_5')
        h1 = UnityHost(_id='Host_1', cli=t_rest())
        resp = share.allow_read_only_access([h1, '1.1.1.1'],
                                            force_create_host=True)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_share_in_tenant_allow_access_to_ip(self):
        share = UnityNfsShare(_id='NFSShare_32', cli=t_rest())
        resp = share.allow_read_only_access('192.168.112.23')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_access_success(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_7')
        resp = share.delete_access(['Host_1', 'Host_14', 'Host_15'])
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_access_ip_not_found(self):
        def f():
            share = UnityNfsShare(cli=t_rest(), _id='NFSShare_7')
            share.delete_access(['9.9.9.9'])

        assert_that(f, raises(UnityHostNotFoundException, 'not found'))

    @patch_rest
    def test_delete_access_host_not_found(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_4')
        resp = share.delete_access(['Host_99'])
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_clear_access(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_7')
        resp = share.clear_access()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_add_read_only_snap_share(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_30')
        resp = share.allow_read_only_access('1.1.1.1', True)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_add_read_write_snap_share(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_30')
        resp = share.allow_read_write_access('2.2.2.2', True)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_access_snap_share(self):
        share = UnityNfsShare(cli=t_rest(), _id='NFSShare_31')
        resp = share.delete_access(['1.1.1.1', '1.1.1.3'])
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_snap_based_share_properties(self):
        share = UnityNfsShare.get(t_rest(), _id='NFSShare_2')
        assert_that(share.type, equal_to(NFSTypeEnum.NFS_SNAPSHOT))
        assert_that(share.filesystem, instance_of(UnityFileSystem))
        assert_that(share.snap, instance_of(UnitySnap))


class UnityNfsHostConfigTest(TestCase):
    def test_add_ro(self):
        config = UnityNfsHostConfig(
            no_access=[host('Host_1'), host('Host_9')])
        config.allow_ro(host('Host_1'), host('Host_11'))
        config.allow_rw(host('Host_9'))

        assert_that(config.root,
                    only_contains(host('Host_1'),
                                  host('Host_9'),
                                  host('Host_11')))
        assert_that(config.ro,
                    only_contains(host('Host_1'),
                                  host('Host_11')))
        assert_that(config.rw, only_contains(host('Host_9')))
        assert_that(len(config.no_access), equal_to(0))

    def test_add_same_twice(self):
        config = UnityNfsHostConfig(no_access=[host('Host_9')])
        config.allow_rw(host('Host_9'), host('Host_9'))
        config.allow_rw(host('Host_9'))
        assert_that(len(config.rw), equal_to(1))
        assert_that(config.rw, only_contains(host('Host_9')))
        assert_that(config.no_access, equal_to([]))
        assert_that(config.ro, none())
        assert_that(config.root, only_contains(host('Host_9')))

    def test_clear_access_all(self):
        config = UnityNfsHostConfig(no_access=[host('Host_9')])
        config.allow_rw(host('Host_1'))
        config.clear_all()
        assert_that(len(config.rw), equal_to(0))
        assert_that(len(config.ro), equal_to(0))
        assert_that(len(config.no_access), equal_to(0))
        assert_that(len(config.root), equal_to(0))

    def test_clear_access_with_white_list(self):
        config = UnityNfsHostConfig(no_access=[host('Host_9')])
        config.allow_rw(host('Host_1'), host('Host_2'))
        config.allow_root(host('Host_1'), host('Host_2'), host('Host_3'))
        config.clear_all(host('Host_1'), host('Host_4'), host('Host_9'))
        assert_that(len(config.rw), equal_to(0))
        assert_that(len(config.ro), equal_to(0))
        assert_that(len(config.no_access), equal_to(1))
        assert_that(len(config.root), equal_to(1))
