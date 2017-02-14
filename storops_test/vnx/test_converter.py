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

from hamcrest import assert_that, equal_to, none, instance_of

from storops.vnx import converter
from storops.vnx.resource.lun import VNXLun, VNXLunList
from storops.vnx.resource.snap import VNXSnap
from storops_test.vnx.cli_mock import t_cli, patch_cli

__author__ = 'Cedric Zhuang'


class ConverterTest(TestCase):
    def test_id_to_lun_normal(self):
        lun = converter.id_to_lun('12')
        assert_that(lun, instance_of(VNXLun))
        assert_that(lun.get_id(lun), equal_to(12))

    def test_id_to_lun_na(self):
        lun = converter.id_to_lun('N/A')
        assert_that(lun, none())

    def test_id_to_lun_none(self):
        lun = converter.id_to_lun(None)
        assert_that(lun, none())

    def test_name_to_lun_na(self):
        lun = converter.name_to_lun('N/A')
        assert_that(lun, none())

    def test_name_to_lun_normal(self):
        lun = converter.name_to_lun('abc')
        assert_that(lun._name, equal_to('abc'))

    def name_to_snap(self):
        snap = converter.name_to_snap('abc')
        assert_that(snap, instance_of(VNXSnap))
        assert_that(snap._name, equal_to('abc'))

    def test_name_to_snap_na(self):
        snap = converter.name_to_snap('N/A')
        assert_that(snap, none())

    @patch_cli
    def test_ids_to_lun_list_normal(self):
        lun_list = converter.ids_to_lun_list('0,1,2')
        lun_list._cli = t_cli()
        assert_that(lun_list, instance_of(VNXLunList))
        assert_that(len(lun_list), equal_to(3))

    def test_ids_to_lun_list_empty(self):
        lun_list = converter.ids_to_lun_list('')
        assert_that(len(lun_list), equal_to(0))
        lun_list = converter.ids_to_lun_list(None)
        assert_that(len(lun_list), equal_to(0))

    @patch_cli
    def test_indices_to_disk_list_normal(self):
        value = '''Bus 0 Enclosure 0  Disk A0
                   Bus 0 Enclosure 0  Disk A4'''
        disks = converter.indices_to_disk_list(value)
        disks._cli = t_cli()
        assert_that(len(disks), equal_to(2))

    def test_indices_to_disk_list_empty(self):
        disks = converter.indices_to_disk_list('')
        assert_that(len(disks), equal_to(0))
