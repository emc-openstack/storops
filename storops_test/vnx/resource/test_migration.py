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

from hamcrest import assert_that, equal_to, instance_of, raises

from storops.exception import VNXLunNotMigratingError, VNXLunSyncCompletedError
from storops.vnx.resource.lun import VNXLun
from storops_test.vnx.cli_mock import t_cli, patch_cli
from storops.vnx.enums import VNXMigrationRate
from storops.vnx.resource.migration import VNXMigrationSession

__author__ = 'Cedric Zhuang'


class VNXMigrationSessionTest(TestCase):
    @patch_cli
    def test_properties(self):
        ms = VNXMigrationSession(0, t_cli())
        assert_that(ms.source_lu_id, equal_to(0))
        assert_that(ms.source_lu_name, equal_to('LUN 0'))
        assert_that(ms.dest_lu_id, equal_to(1))
        assert_that(ms.dest_lu_name, equal_to('LUN 1'))
        assert_that(ms.migration_rate, equal_to(VNXMigrationRate.HIGH))
        assert_that(ms.percent_complete, equal_to(50.0))
        assert_that(ms.time_remaining, equal_to('0 second(s)'))
        assert_that(ms.current_state, equal_to('MIGRATING'))
        assert_that(ms.is_migrating, equal_to(True))
        assert_that(ms.is_success, equal_to(False))
        assert_that(ms.existed, equal_to(True))

    @patch_cli
    def test_source_lun(self):
        ms = VNXMigrationSession(0, t_cli())
        lun = ms.source_lun
        assert_that(lun, instance_of(VNXLun))
        assert_that(lun.get_id(lun), equal_to(ms.source_lu_id))

    @patch_cli
    def test_destination_lun(self):
        ms = VNXMigrationSession(0, t_cli())
        lun = ms.destination_lun
        assert_that(lun, instance_of(VNXLun))
        assert_that(lun.get_id(lun), equal_to(ms.dest_lu_id))

    @patch_cli
    def test_get_all(self):
        ms_list = VNXMigrationSession.get(t_cli())
        assert_that(len(ms_list), equal_to(2))

    @patch_cli(output='migrate_-list_none.txt')
    def test_get_all_none(self):
        ms_list = VNXMigrationSession.get(t_cli())
        assert_that(len(ms_list), equal_to(0))

    @patch_cli
    def test_get_no_session(self):
        ms = VNXMigrationSession(10, t_cli())
        assert_that(ms.existed, equal_to(False))
        assert_that(ms.is_migrating, equal_to(False))
        assert_that(ms.is_success, equal_to(True))

    @patch_cli
    def test_get_lun_not_exists(self):
        ms = VNXMigrationSession(1234, t_cli())
        assert_that(ms.existed, equal_to(False))

    @patch_cli
    def test_cancel_migrate(self):
        def f():
            ms = VNXMigrationSession(0, t_cli())
            ms.cancel()

        assert_that(f, raises(VNXLunNotMigratingError,
                              'not currently migrating'))

    @patch_cli
    def test_cancel_migrate_sync_completed(self):
        def f():
            ms = VNXMigrationSession(1, t_cli())
            ms.cancel()

        assert_that(f, raises(VNXLunSyncCompletedError,
                              'because data sychronization is completed'))
