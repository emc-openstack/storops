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

from hamcrest import assert_that, equal_to, instance_of

from storops.unity.enums import StorageResourceTypeEnum, ReplicationTypeEnum, \
    ThinStatusEnum, TieringPolicyEnum
from storops.unity.resource.filesystem import UnityFileSystem
from storops.unity.resource.health import UnityHealth
from storops.unity.resource.pool import UnityPoolList
from storops.unity.resource.storage_resource import UnityStorageResource, \
    UnityStorageResourceList
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityStorageResourceTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        sr = UnityStorageResource(_id='res_27', cli=t_rest())
        assert_that(sr.id, equal_to('res_27'))
        assert_that(sr.type, equal_to(StorageResourceTypeEnum.FILE_SYSTEM))
        assert_that(sr.replication_type, equal_to(ReplicationTypeEnum.NONE))
        assert_that(sr.thin_status, equal_to(ThinStatusEnum.TRUE))
        assert_that(sr.relocation_policy,
                    equal_to(TieringPolicyEnum.AUTOTIER_HIGH))
        assert_that(sr.health, instance_of(UnityHealth))
        assert_that(sr.name, equal_to('fs3'))
        assert_that(sr.description, equal_to(''))
        assert_that(sr.is_replication_destination, equal_to(False))
        assert_that(sr.size_total, equal_to(3221225472))
        assert_that(sr.size_used, equal_to(1620303872))
        assert_that(sr.size_allocated, equal_to(3221225472))
        assert_that(sr.per_tier_size_used, equal_to([6442450944, 0, 0]))
        assert_that(sr.metadata_size, equal_to(3489660928))
        assert_that(sr.metadata_size_allocated, equal_to(3221225472))
        assert_that(sr.snaps_size_total, equal_to(0))
        assert_that(sr.snaps_size_allocated, equal_to(0))
        assert_that(sr.snap_count, equal_to(0))
        assert_that(sr.pools, instance_of(UnityPoolList))
        assert_that(sr.filesystem, instance_of(UnityFileSystem))

    @patch_rest
    def test_get_all(self):
        sr_list = UnityStorageResourceList(cli=t_rest())
        assert_that(len(sr_list), equal_to(10))
