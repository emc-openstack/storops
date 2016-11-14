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

from hamcrest import assert_that, equal_to, instance_of, contains_string, \
    has_item

from storops.exception import UnityFileSystemSizeTooSmallError
from storops.unity.enums import JobStateEnum, JobTaskStateEnum
from storops.unity.resource.job import UnityJob, UnityJobList, \
    UnityJobTaskList, \
    UnityMessageList, UnityLocalizedMessageList
from storops.unity.resource.pool import UnityPool
from storops.unity.resource.nas_server import UnityNasServer
from storops import exception as ex

from test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityJobTest(TestCase):
    @staticmethod
    def test_job():
        return UnityJob(_id='N-345', cli=t_rest())

    @patch_rest
    def test_job_properties(self):
        job = self.test_job()
        assert_that(job.id, equal_to('N-345'))
        assert_that(job.state, equal_to(JobStateEnum.COMPLETED))
        assert_that(job.description, equal_to('Delete storage resource'))
        end_time = '2016-03-22 10:39:53.561000+00:00'
        assert_that(str(job.state_change_time), equal_to(end_time))
        assert_that(str(job.end_time), equal_to(end_time))
        assert_that(str(job.submit_time),
                    equal_to('2016-03-22 10:39:20.033000+00:00'))
        assert_that(str(job.start_time),
                    equal_to('2016-03-22 10:39:20.184000+00:00'))
        assert_that(job.progress_pct, equal_to(100))
        assert_that(str(job.elapsed_time), equal_to('0:00:33.377000'))

    @patch_rest
    def test_task_properties(self):
        job = self.test_job()
        tasks = job.tasks
        assert_that(tasks, instance_of(UnityJobTaskList))
        assert_that(len(tasks), equal_to(4))

        task = tasks[0]
        assert_that(task.state, equal_to(JobTaskStateEnum.COMPLETED))
        assert_that(task.name, equal_to(
            'job.applicationprovisioningservice.task.'
            'DeleteApplicationPrecondition613'))
        assert_that(task.description,
                    equal_to('Check storage resource state before deletion'))
        assert_that(task.parameters_in, instance_of(dict))
        assert_that(task.parameters_in['deleteRemotePeer'], equal_to(True))
        assert_that(task.parameters_in['id'], equal_to('RS_1'))
        assert_that(task.parameters_out, instance_of(dict))
        assert_that(task.parameters_out['id'], equal_to('B-2'))

    @patch_rest
    def test_message_properties(self):
        job = self.test_job()
        messages = job.tasks[0].messages
        assert_that(messages, instance_of(UnityMessageList))
        assert_that(len(messages), equal_to(2))

        message = messages[0]
        assert_that(message.error_code, equal_to(0))

        localized_messages = message.messages
        assert_that(localized_messages, instance_of(UnityLocalizedMessageList))

        localized_message = localized_messages[0]
        assert_that(localized_message.locale, equal_to('en_US'))
        assert_that(localized_message.message, equal_to('Success'))

    @patch_rest
    def test_get_all(self):
        jobs = UnityJobList(cli=t_rest())
        assert_that(len(jobs), equal_to(3))

    @patch_rest
    def test_create_nfs_share_async(self):
        pool = UnityPool.get(cli=t_rest(), _id='pool_5')
        nas_server = UnityNasServer.get(cli=t_rest(), _id='nas_6')
        job = UnityJob.create_nfs_share(
            cli=t_rest(), pool=pool, nas_server=nas_server,
            name='513dd8b0-2c22-4da0-888e-494d320303b6',
            size=4294967296)
        assert_that(JobStateEnum.COMPLETED, equal_to(job.state))

    @patch_rest
    def test_create_nfs_share_failed(self):
        pool = UnityPool.get(cli=t_rest(), _id='pool_5')
        nas_server = UnityNasServer.get(cli=t_rest(), _id='nas_6')
        self.assertRaisesRegexp(
            ex.JobStateError,
            'Job State: FAILED.  Error Detail: ',
            UnityJob.create_nfs_share,
            cli=t_rest(), pool=pool, nas_server=nas_server,
            name='613dd8b0-2c22-4da0-888e-494d320303b7',
            size=4294967296,
            async=False)

    @patch_rest
    def test_messages(self):
        job = UnityJob(_id='B-3', cli=t_rest())
        assert_that(len(job.messages), equal_to(1))
        assert_that(job.messages[0], contains_string('too small'))

    @patch_rest
    def test_has_exceptions(self):
        job = UnityJob(_id='B-3', cli=t_rest())
        assert_that(len(job.exceptions), equal_to(1))
        exception = job.exceptions[0]
        assert_that(exception,
                    instance_of(UnityFileSystemSizeTooSmallError))
        assert_that(str(exception), contains_string('too small'))
        assert_that(job.has_exception(), equal_to(True))

    @patch_rest
    def test_batch_without_error(self):
        job = UnityJob(_id='B-693', cli=t_rest())
        assert_that(job.messages, has_item('Success'))
        assert_that(len(job.exceptions), equal_to(0))
        assert_that(job.has_exception(), equal_to(False))

    @patch_rest
    def test_normal_without_error(self):
        job = UnityJob(_id='N-345', cli=t_rest())
        assert_that(job.messages, has_item('Success'))
        assert_that(len(job.exceptions), equal_to(0))
