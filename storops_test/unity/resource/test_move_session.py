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

from hamcrest import assert_that
from hamcrest import equal_to

from storops.unity.enums import MoveSessionStateEnum, MoveSessionStatusEnum, \
    MoveSessionPriorityEnum
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.move_session import UnityMoveSession
from storops.unity.resource.pool import UnityPool
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Yong Huang'


class UnityMoveSessionTest(TestCase):
    @patch_rest
    def test_get_move_session_property(self):
        move_session = UnityMoveSession(_id='move_27', cli=t_rest())
        assert_that(move_session.existed, equal_to(True))
        assert_that(move_session.id, equal_to('move_27'))
        assert_that(move_session.state,
                    equal_to(MoveSessionStateEnum.COMPLETED))
        assert_that(move_session.status,
                    equal_to(MoveSessionStatusEnum.INITIALIZING))
        assert_that(move_session.priority,
                    equal_to(MoveSessionPriorityEnum.NORMAL))
        assert_that(move_session.progress_pct, equal_to(100))
        assert_that(move_session.current_transfer_rate, equal_to(0))
        assert_that(move_session.avg_transfer_rate, equal_to(5120))
        assert_that(move_session.est_time_remaining, equal_to("00:00:00.000"))
        assert_that(move_session.source_storage_resource.id, equal_to("sv_18"))
        assert_that(move_session.destination_pool.id, equal_to("pool_1"))

    @patch_rest
    def test_create_move_session(self):
        cli = t_rest()
        lun = UnityLun.get(cli=cli, _id='sv_18')
        dest_pool = UnityPool.get(cli=cli, _id='pool_5')
        move_session = UnityMoveSession.create(
            cli=cli,
            source_storage_resource=lun,
            destination_pool=dest_pool,
            is_dest_thin=True,
            is_data_reduction_applied=True,
            priority=5)
        assert_that(move_session.id, equal_to('move_32'))
        assert_that(move_session.state,
                    equal_to(MoveSessionStateEnum.RUNNING))
        assert_that(move_session.status,
                    equal_to(MoveSessionStatusEnum.INITIALIZING))
        assert_that(move_session.priority,
                    equal_to(MoveSessionPriorityEnum.HIGH))

    @patch_rest
    def test_modify_move_session(self):
        cli = t_rest()
        move_session = UnityMoveSession(_id='move_32', cli=t_rest())
        move_session = move_session.modify(cli, priority=4)
        assert_that(move_session.is_ok(), equal_to(True))

    @patch_rest
    def test_cancel_move_session(self):
        move_session = UnityMoveSession(_id='move_32', cli=t_rest())
        resp = move_session.cancel()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_create_move_session_to_thick(self):
        cli = t_rest()
        lun = UnityLun.get(cli=cli, _id='sv_19')
        dest_pool = UnityPool.get(cli=cli, _id='pool_6')
        move_session = UnityMoveSession.create(
            cli=cli,
            source_storage_resource=lun,
            destination_pool=dest_pool,
            is_dest_thin=False,
            is_data_reduction_applied=False,
            priority=5)
        assert_that(move_session.id, equal_to('move_35'))
        assert_that(move_session.state,
                    equal_to(MoveSessionStateEnum.COMPLETED))
        assert_that(move_session.status,
                    equal_to(MoveSessionStatusEnum.INITIALIZING))
        assert_that(move_session.priority,
                    equal_to(MoveSessionPriorityEnum.NORMAL))
