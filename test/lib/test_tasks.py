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

import shutil
from unittest import TestCase
import tempfile
from hamcrest import assert_that, equal_to

from storops.lib import tasks
from test.vnx.cli_mock import patch_cli, t_vnx
import time


class TestPQueue(TestCase):
    def setUp(self):
        self.path = tempfile.mkdtemp(suffix='storops')
        self.q = tasks.PQueue(self.path)

    def tearDown(self):
        self.q.stop()
        self.q = None
        time.sleep(0.1)
        shutil.rmtree(self.path, ignore_errors=True)

    def test_queue_path(self):
        assert_that(self.q.path, equal_to(self.path))

    def test_put(self):
        fake_vnx = t_vnx()
        self.q.put(fake_vnx.delete_lun, name='l1')

    def test_get(self):
        fake_vnx = t_vnx()
        self.q.put(fake_vnx.delete_lun, name='l1')

        pickled_item = self.q.get()
        assert_that(pickled_item['object']._ip, equal_to(fake_vnx._ip))
        assert_that(pickled_item['method'], equal_to('delete_lun'))
        assert_that(pickled_item['params']['name'], equal_to('l1'))

    def test_run_empty_queue(self):
        self.q.set_interval(0.01)
        self.q.start()
        # Make sure restart is fine
        self.q.start()

    @patch_cli
    def test_run_tasks(self):
        self.q.set_interval(0.01)
        fake_vnx = t_vnx()
        self.q.put(fake_vnx.delete_lun, name='l1')
        self.q.start()

    def test_re_enqueue(self):
        fake_vnx = t_vnx()
        item = {'object': fake_vnx, 'method': 'delete_lun',
                'params': {'name': 'l1'}}
        self.q.re_enqueue(item)
        assert_that(item['retries'], equal_to(1))

    def test_re_enqueue_max_retries(self):
        fake_vnx = t_vnx()
        item = {'object': fake_vnx, 'method': 'delete_lun', 'params': 'l1'}
        for i in range(100):
            self.q.re_enqueue(item)
            self.q.get()

        self.q.re_enqueue(item)
        assert_that(item['retries'], equal_to(100))

    @patch_cli
    def test_enqueue_expected_error(self):
        self.q.set_interval(0.1)
        fake_vnx = t_vnx()
        uid = '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:01'
        self.q.put(fake_vnx.delete_hba, hba_uid=uid)
        self.q.start()
        time.sleep(0.2)
        reenqueued_item = self.q.get()
        assert_that(None, equal_to(reenqueued_item))

    @patch_cli
    def test_enqueue_storops_error(self):
        self.q.set_interval(0.1)
        fake_vnx = t_vnx()
        self.q.put(fake_vnx.create_block_user,
                   name='b', password='b', role='operator')
        self.q.start()
        time.sleep(0.2)
        reenqueued_item = self.q.get()
        assert_that('b', equal_to(reenqueued_item['params']['name']))
