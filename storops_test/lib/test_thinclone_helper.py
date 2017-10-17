# coding=utf-8
# Copyright (c) 2017 Dell Inc. or its subsidiaries.
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

import shutil
import tempfile
from unittest import TestCase

import mock
from hamcrest import assert_that, equal_to, raises

import storops
from storops.exception import UnityThinCloneLimitExceededError
from storops.lib.thinclone_helper import TCHelper
from storops.unity.enums import ThinCloneActionEnum
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.snap import UnitySnap
from storops_test.unity.rest_mock import patch_rest, t_rest


class TestThinCloneHelper(TestCase):
    @classmethod
    def setUpClass(cls):
        storops.enable_log()

    def setUp(self):
        self.path = tempfile.mkdtemp(suffix='storops')
        TCHelper.set_up(self.path)
        TCHelper._gc_background.set_interval(0.10)
        TCHelper._gc_background.MAX_RETRIES = 1

    def tearDown(self):
        shutil.rmtree(self.path, ignore_errors=True)
        TCHelper.clean_up()

    @patch_rest
    def test_thin_clone_lun(self):
        lun = UnityLun.get(_id='sv_2', cli=t_rest(version='4.2.0'))
        cloned = TCHelper.thin_clone(lun._cli, lun, name='test_thin_clone_lun',
                                     description='description',
                                     io_limit_policy=None)
        assert_that(cloned.id, equal_to('sv_5555'))

    @patch_rest
    def test_thin_clone_lun_new_tc_base(self):
        TCHelper._tc_cache['sv_2'] = UnityLun.get(_id='sv_5605',
                                                  cli=t_rest(version='4.2.0'))
        lun = UnityLun.get(_id='sv_2', cli=t_rest(version='4.2.0'))
        cloned = TCHelper.thin_clone(lun._cli, lun, name='test_thin_clone_lun',
                                     description='description',
                                     io_limit_policy=None)
        assert_that(cloned.id, equal_to('sv_5556'))

    @patch_rest
    def test_thin_clone_snap(self):
        snap = UnitySnap.get(_id='38654700002', cli=t_rest(version='4.2.0'))
        cloned = TCHelper.thin_clone(snap._cli, snap,
                                     name='test_thin_clone_snap',
                                     description='description',
                                     io_limit_policy=None)
        assert_that(cloned.id, equal_to('sv_5557'))

    @patch_rest
    def test_thin_clone_snap_new_tc_base(self):
        TCHelper._tc_cache['sv_2'] = UnityLun.get(_id='sv_5605',
                                                  cli=t_rest(version='4.2.0'))
        lun = UnityLun.get(_id='sv_2', cli=t_rest(version='4.2.0'))
        cloned = TCHelper.thin_clone(lun._cli, lun, name='test_thin_clone_lun',
                                     description='description',
                                     io_limit_policy=None)
        assert_that(cloned.id, equal_to('sv_5556'))

    @patch_rest
    def test_thin_clone_limit_exceeded(self):
        lun = UnityLun.get(_id='sv_2', cli=t_rest(version='4.2.0'))

        def _inner():
            TCHelper.thin_clone(lun._cli, lun,
                                name='test_thin_clone_limit_exceeded',
                                description='This is description.',
                                io_limit_policy=None)

        assert_that(_inner, raises(UnityThinCloneLimitExceededError))

    @patch_rest
    def test_notify_dd_copy(self):
        lun = UnityLun.get(_id='sv_2', cli=t_rest(version='4.2.0'))
        copied_lun = UnityLun.get(_id='sv_3', cli=t_rest(version='4.2.0'))

        TCHelper.notify(lun, ThinCloneActionEnum.DD_COPY, copied_lun)
        self.assertTrue(lun.get_id() in TCHelper._tc_cache)
        self.assertEqual(copied_lun, TCHelper._tc_cache[lun.get_id()])
        self.assertFalse(lun.get_id() in TCHelper._gc_candidates)

    @patch_rest
    def test_notify_dd_copy_gc_background(self):
        lun = UnityLun.get(_id='sv_2', cli=t_rest(version='4.2.0'))
        copied_lun = UnityLun.get(_id='sv_3', cli=t_rest(version='4.2.0'))
        old_lun = UnityLun.get(_id='sv_4', cli=t_rest(version='4.2.0'))
        TCHelper._tc_cache[lun.get_id()] = old_lun
        TCHelper.notify(lun, ThinCloneActionEnum.DD_COPY, copied_lun)
        self.assertTrue(lun.get_id() in TCHelper._tc_cache)
        self.assertEqual(copied_lun, TCHelper._tc_cache[lun.get_id()])
        self.assertTrue(old_lun.get_id() in TCHelper._gc_candidates)

    @mock.patch('storops.lib.thinclone_helper.TCHelper._gc_background.put')
    @patch_rest
    def test_notify_dd_copy_gc(self, mocked_put):
        lun = UnityLun.get(_id='sv_2', cli=t_rest(version='4.2.0'))
        copied_lun = UnityLun.get(_id='sv_3', cli=t_rest(version='4.2.0'))
        old_lun = UnityLun.get(_id='sv_4', cli=t_rest(version='4.2.0'))
        TCHelper._tc_cache[lun.get_id()] = old_lun

        TCHelper.notify(lun, ThinCloneActionEnum.DD_COPY, copied_lun)
        self.assertTrue(lun.get_id() in TCHelper._tc_cache)
        self.assertEqual(copied_lun, TCHelper._tc_cache[lun.get_id()])
        self.assertTrue(old_lun.get_id() in TCHelper._gc_candidates)
        mocked_put.assert_called_with(TCHelper._delete_base_lun,
                                      base_lun=old_lun)

    @patch_rest
    def test_notify_lun_attach(self):
        lun = UnityLun.get(_id='sv_2', cli=t_rest(version='4.2.0'))

        TCHelper.notify(lun, ThinCloneActionEnum.LUN_ATTACH)
        self.assertFalse(lun.get_id() in TCHelper._tc_cache)
        self.assertFalse(lun.get_id() in TCHelper._gc_candidates)

    @mock.patch('storops.lib.thinclone_helper.TCHelper._gc_background.put')
    @patch_rest
    def test_notify_lun_attach_gc(self, mocked_put):
        lun = UnityLun.get(_id='sv_2', cli=t_rest(version='4.2.0'))
        old_lun = UnityLun.get(_id='sv_4', cli=t_rest(version='4.2.0'))
        TCHelper._tc_cache[lun.get_id()] = old_lun

        TCHelper.notify(lun, ThinCloneActionEnum.LUN_ATTACH)
        self.assertFalse(lun.get_id() in TCHelper._tc_cache)
        self.assertTrue(old_lun.get_id() in TCHelper._gc_candidates)
        mocked_put.assert_called_with(TCHelper._delete_base_lun,
                                      base_lun=old_lun)

    @mock.patch('storops.unity.resource.lun.UnityLun.delete')
    @patch_rest
    def test_notify_tc_delete_base_lun_still_using(self, lun_delete):
        lun = UnityLun.get(_id='sv_5600', cli=t_rest(version='4.2.0'))

        TCHelper.notify(lun, ThinCloneActionEnum.TC_DELETE)
        self.assertFalse(lun.get_id() in TCHelper._tc_cache)
        self.assertFalse(lun.get_id() in TCHelper._gc_candidates)
        lun_delete.assert_not_called()

    @mock.patch('storops.lib.thinclone_helper.TCHelper._gc_background.put')
    @mock.patch('storops.unity.resource.lun.UnityLun.delete')
    @patch_rest
    def test_notify_tc_delete_base_lun_having_thinclone(self, mocked_put,
                                                        lun_delete):
        lun = UnityLun.get(_id='sv_5602', cli=t_rest(version='4.2.0'))
        base_lun = UnityLun.get(_id='sv_5603', cli=t_rest(version='4.2.0'))
        TCHelper._gc_candidates[base_lun.get_id()] = base_lun.get_id()

        TCHelper.notify(lun, ThinCloneActionEnum.TC_DELETE)
        self.assertFalse(lun.get_id() in TCHelper._tc_cache)
        self.assertFalse(lun.get_id() in TCHelper._gc_candidates)
        self.assertTrue(base_lun.get_id() in TCHelper._gc_candidates)
        lun_delete.assert_not_called()

    @patch_rest
    def test_notify_tc_delete_base_lun_snap_under_destroying(self):
        lun = UnityLun.get(_id='sv_5606', cli=t_rest(version='4.2.0'))
        base_lun = UnityLun.get(_id='sv_5607', cli=t_rest(version='4.2.0'))
        TCHelper._gc_candidates[base_lun.get_id()] = base_lun.get_id()

        TCHelper.notify(lun, ThinCloneActionEnum.TC_DELETE)
        self.assertFalse(lun.get_id() in TCHelper._tc_cache)
        self.assertFalse(lun.get_id() in TCHelper._gc_candidates)
        self.assertTrue(base_lun.get_id() in TCHelper._gc_candidates)

    @mock.patch('storops.unity.resource.lun.UnityLun.delete')
    @patch_rest
    def test_notify_tc_delete_base_lun_ready_for_gc(self, lun_delete):
        lun = UnityLun.get(_id='sv_5600', cli=t_rest(version='4.2.0'))
        base_lun = UnityLun.get(_id='sv_5601', cli=t_rest(version='4.2.0'))
        TCHelper._gc_candidates[base_lun.get_id()] = base_lun.get_id()

        TCHelper.notify(lun, ThinCloneActionEnum.TC_DELETE)
        self.assertFalse(lun.get_id() in TCHelper._tc_cache)
        self.assertFalse(lun.get_id() in TCHelper._gc_candidates)
        self.assertFalse(base_lun.get_id() in TCHelper._gc_candidates)
        lun_delete.assert_called_once()

    @mock.patch('storops.lib.thinclone_helper.TCHelper._gc_background.put')
    @patch_rest
    def test_notify_tc_delete_base_lun(self, mocked_put):
        base_lun = UnityLun.get(_id='sv_5608', cli=t_rest(version='4.2.0'))

        TCHelper.notify(base_lun, ThinCloneActionEnum.BASE_LUN_DELETE)
        self.assertTrue(base_lun.get_id() in TCHelper._gc_candidates)
        mocked_put.assert_called_with(TCHelper._delete_base_lun,
                                      base_lun=base_lun)
