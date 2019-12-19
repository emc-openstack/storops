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

import threading
from collections import OrderedDict
from unittest import TestCase

from hamcrest import assert_that, equal_to, instance_of, raises
from mock import patch

from storops.exception import JobStateError, JobTimeoutException
from storops.lib import job_helper
from storops.unity.resource.job import UnityJob
from storops_test.unity.rest_mock import t_rest, patch_rest


class MockJob(object):
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class TestJobHelper(TestCase):
    def setUp(self):
        self.jh = job_helper.JobHelper(cli=t_rest())

    def tearDown(self):
        self.jh.jobs = OrderedDict()

    def test_add_job(self):
        job_id = 'N-101'
        job = MockJob(id=job_id)
        self.jh.add_job(job)
        assert_that(self.jh.jobs[job_id].id, equal_to(job_id))

    def test_add_existed_job(self):
        job_id = 'N-102'
        job = MockJob(id=job_id)
        self.jh.add_job(job)
        self.jh.add_job(job)
        assert_that(self.jh.jobs[job_id].id, equal_to(job_id))

    def test_remove_job(self):
        job_id = 'N-103'
        job = MockJob(id=job_id)
        self.jh.jobs[job_id] = job
        self.jh.remove_job(job)
        ret = job_id in self.jh.jobs
        assert_that(ret, equal_to(False))

    def test_remove_nonexisted_job(self):
        job_id = 'N-104'
        job = MockJob(id=job_id)
        self.jh.remove_job(job)
        ret = job_id in self.jh.jobs
        assert_that(ret, equal_to(False))

    def test_get_job(self):
        job_id = 'N-105'
        job = MockJob(id=job_id)
        self.jh.jobs[job_id] = job
        assert_that(self.jh.get_job(job).id, equal_to(job_id))

    def test_get_nonexisted_job(self):
        job_id = 'N-106'
        job = MockJob(id=job_id)
        assert_that(self.jh.get_job(job), equal_to(None))

    @patch_rest
    def test_wait_job(self):
        job_id = 'N-3078'
        job = UnityJob(_id=job_id, cli=t_rest())
        new_job = self.jh.wait_job(job, 10, 3)
        assert_that(new_job.id, equal_to(job_id))
        assert_that(new_job.state.index, equal_to(4))
        ret = job_id in self.jh.jobs
        assert_that(ret, equal_to(False))

    @patch_rest
    def test_wait_job_state_error(self):
        job_id = 'N-3079'

        def f():
            job = UnityJob(_id=job_id, cli=t_rest())
            self.jh.wait_job(job, 10, 3)

        assert_that(f, raises(JobStateError))
        ret = job_id in self.jh.jobs
        assert_that(ret, equal_to(False))

    @patch_rest
    def test_wait_job_state_timeout(self):
        job_id = 'N-3080'

        def f():
            job = UnityJob(_id=job_id, cli=t_rest())
            self.jh.wait_job(job, 3, 1)

        assert_that(f, raises(JobTimeoutException))
        ret = job_id in self.jh.jobs
        assert_that(ret, equal_to(False))

    @patch_rest
    def test__query_jobs(self):
        job_1 = MockJob(id='N-3074')
        job_2 = MockJob(id='N-3075')
        job_3 = MockJob(id='N-3076')
        self.jh.add_job(job_1)
        self.jh.add_job(job_2)
        self.jh.add_job(job_3)
        self.jh._query_jobs()
        new_job_1 = self.jh.get_job(job_1)
        new_job_2 = self.jh.get_job(job_2)
        new_job_3 = self.jh.get_job(job_3)
        assert_that(new_job_1.id, equal_to(job_1.id))
        assert_that(new_job_1.state.index, equal_to(4))
        assert_that(new_job_2.id, equal_to(job_2.id))
        assert_that(new_job_2.state.index, equal_to(4))
        assert_that(new_job_3.id, equal_to(job_3.id))
        assert_that(new_job_3.state.index, equal_to(4))

    def test__query_jobs_no_job(self):
        self.jh.jobs = OrderedDict()
        self.jh._query_jobs()
        assert_that(self.jh.jobs, equal_to(OrderedDict()))

    def test_start(self):
        self.jh.start()
        assert_that(self.jh.started, equal_to(True))
        assert_that(self.jh.t, instance_of(threading.Thread))
        assert_that(self.jh.t.daemon, equal_to(True))


class TestGetJobHelper(TestCase):
    @patch('threading.Thread')
    def test_get_job_helper(self, mocked_thread):
        jh = job_helper.get_job_helper(cli=t_rest())
        assert_that(jh.jobs, equal_to(OrderedDict()))
        assert_that(jh.started, equal_to(True))
