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

from hamcrest import assert_that, equal_to, has_item, raises, only_contains

from storops.vnx.parsers import get_vnx_parser
from storops_test.vnx.cli_mock import patch_cli, t_cli
from storops.exception import VNXConsistencyGroupError, \
    VNXConsistencyGroupNameInUseError, VNXConsistencyGroupNotFoundError, \
    VNXSnapNameInUseError
from storops.vnx.resource.cg import VNXConsistencyGroup
from storops.vnx.resource.cg import VNXConsistencyGroupList
from storops.vnx.resource.lun import VNXLun

__author__ = 'Cedric Zhuang'


class VNXConsistencyGroupListTest(TestCase):
    @patch_cli
    def test_parse(self):
        assert_that(len(VNXConsistencyGroupList(t_cli())), equal_to(2))

    @patch_cli
    def test_delete_not_existed_member(self):
        lun = VNXLun(name='y', cli=t_cli())
        cg_list = VNXConsistencyGroupList(t_cli())
        # no error raised
        cg_list.delete_member(lun)


class VNXConsistencyGroupTest(TestCase):
    @patch_cli
    def test_list_consistency_group(self):
        cg_list = VNXConsistencyGroup.get(t_cli())
        assert_that(len(cg_list), equal_to(2))
        assert_that(cg_list.name, only_contains('another cg', 'test cg name'))

    @patch_cli
    def test_update_consistency_group_list_member(self):
        cg_list = VNXConsistencyGroup.get(t_cli())
        cg = cg_list[1]
        name = cg.name
        cg.update()
        assert_that(cg.name, equal_to(name))

    @patch_cli
    def test_properties(self):
        cg = VNXConsistencyGroup(name="test_cg", cli=t_cli())
        assert_that(cg.name, equal_to('test_cg'))
        assert_that(cg.lun_list.lun_id, only_contains(1, 3))
        assert_that(cg.state, equal_to('Ready'))
        assert_that(cg.existed, equal_to(True))

    def test_update(self):
        parser = get_vnx_parser('VNXConsistencyGroup')
        data = {
            parser.NAME.key: 'test cg name',
            parser.LUN_LIST.key: [1, 5, 7],
            parser.STATE.key: 'Offline'
        }

        cg = VNXConsistencyGroup()
        cg.update(data)

        assert_that(cg.name, equal_to('test cg name'))
        assert_that(cg.lun_list, only_contains(1, 5, 7))
        assert_that(cg.state, equal_to('Offline'))

    def test_parse(self):
        output = """
                Name:  test cg name
                Name:  another cg
                """
        cgs = VNXConsistencyGroup.parse_all(output)
        assert_that(len(cgs), equal_to(2))
        names = [cg.name for cg in cgs]
        assert_that(names, has_item('test cg name'))
        assert_that(names, has_item('another cg'))

    @patch_cli
    def test_add_member(self):
        def f():
            cg = VNXConsistencyGroup('test_cg', t_cli())
            m1 = VNXLun(name='m1', cli=t_cli())
            m2 = VNXLun(name='m2', cli=t_cli())
            cg.add_member(m1, m2)

        assert_that(f, raises(VNXConsistencyGroupError, 'Cannot add members'))

    @patch_cli
    def test_has_member(self):
        cg = VNXConsistencyGroup('test_cg', t_cli())
        lun = VNXLun(lun_id=1)
        assert_that(cg.has_member(lun), equal_to(True))
        assert_that(cg.has_member(7), equal_to(False))

    @patch_cli
    def test_cg_no_poll(self):
        def f():
            cg = VNXConsistencyGroup(name="test_cg", cli=t_cli())
            with cg.with_no_poll():
                cg.add_member(1, 2, 3)

        assert_that(f, raises(VNXConsistencyGroupError, 'does not exist'))

    @patch_cli
    def test_cg_not_found(self):
        def f():
            cg = VNXConsistencyGroup(name="cg1", cli=t_cli())
            cg.add_member(1)

        assert_that(f, raises(VNXConsistencyGroupNotFoundError, 'Cannot find'))

    @patch_cli
    def test_create_cg_name_in_use(self):
        def f():
            VNXConsistencyGroup.create(cli=t_cli(), name='cg0')

        assert_that(f, raises(VNXConsistencyGroupNameInUseError,
                              'already in use'))

    @patch_cli
    def test_delete_cg_not_exists(self):
        def f():
            cg = VNXConsistencyGroup(cli=t_cli(), name='cg0')
            cg.delete()

        assert_that(f, raises(VNXConsistencyGroupNotFoundError, 'Cannot find'))

    @patch_cli
    def test_create_cg_snap_success(self):
        cg = VNXConsistencyGroup(name="cg1", cli=t_cli())
        snap = cg.create_snap('cg1_snap')
        assert_that(snap._name, equal_to('cg1_snap'))
        assert_that(snap.source_luns, only_contains(1))
        assert_that(snap.source_cg, equal_to('cg1'))

    @patch_cli
    def test_create_cg_snap_name_existed(self):
        def f():
            cg = VNXConsistencyGroup(name="cg2", cli=t_cli())
            cg.create_snap('cg1_snap')

        assert_that(f, raises(VNXSnapNameInUseError, 'already in use'))

    @patch_cli
    def test_cg_empty_member_property(self):
        cg = VNXConsistencyGroup(name='cg0', cli=t_cli())
        assert_that(len(cg.lun_list), equal_to(0))
