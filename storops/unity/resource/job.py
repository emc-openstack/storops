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

import retryz
from storops import exception as ex
from storops.exception import get_rest_exception
from storops.lib.common import instance_cache
from storops.unity.resource import UnityResource, UnityResourceList, \
    UnityAttributeResource
from storops.unity.enums import FSSupportedProtocolEnum

import storops
from storops.unity import enums

__author__ = 'Cedric Zhuang'


class UnityJob(UnityResource):
    @classmethod
    def create_nfs_share(cls, cli, pool, nas_server, name, size,
                         is_thin=None,
                         tiering_policy=None, async=True):
        pool_clz = storops.unity.resource.pool.UnityPool
        nas_server_clz = storops.unity.resource.nas_server.UnityNasServer

        pool = pool_clz.get(cli, pool)
        nas_server = nas_server_clz.get(cli, nas_server)
        proto = FSSupportedProtocolEnum.NFS

        job_req_body = {
            'description': 'Creating Filesystem and share',
            'tasks': []
        }
        task_body = {
            'action': 'createFilesystem',
            'description': 'Create File System',
            'name': 'CreateNewFilesystem',
            'object': 'storageResource',
            'parametersIn': {
                'name': name,
                'description': '',
                'fsParameters': {},
                'nfsShareCreate': []
            }
        }
        fs_parameters = {
            'pool': pool,
            'nasServer': nas_server,
            'supportedProtocols': proto,
            'isThinEnabled': is_thin,
            'size': size,
            'fastVPParameters': {
                'tieringPolicy': tiering_policy
            }
        }
        nfs_share_create = {
            'name': name,
            'path': '/',

        }
        task_body['parametersIn']['fsParameters'] = cli.make_body(
            fs_parameters)
        task_body['parametersIn']['nfsShareCreate'].append(
            cli.make_body(nfs_share_create))
        job_req_body['tasks'].append(task_body)

        resp = cli.post(cls().resource_class, **job_req_body)
        resp.raise_if_err()
        job = cls(_id=resp.resource_id, cli=cli)
        if not async:
            job.wait_job_completion()
        return job

    def check_errors(self):
        if self.state == enums.JobStateEnum.COMPLETED:
            return True
        elif self.state in (enums.JobStateEnum.FAILED,
                            enums.JobStateEnum.ROLLING_BACK,
                            enums.JobStateEnum.COMPLETED_WITH_ERROR):
            raise ex.JobStateError(self)
        return False

    def wait_job_completion(self, **kwargs):
        interval = kwargs.pop('interval', 5)
        timeout = kwargs.pop('timeout', 3600)

        @retryz.retry(timeout=timeout, wait=interval, on_return=False)
        def _do_update():
            self.update()
            return self.check_errors()

        try:
            _do_update()
        except retryz.RetryTimeoutError:
            raise ex.JobTimeoutException()

    @property
    @instance_cache
    def _task_messages(self):
        return [task_message
                for task in self.tasks
                for task_message in task.messages]

    @property
    @instance_cache
    def _localized_messages(self):
        return [message
                for messages in self._task_messages
                for message in messages.messages]

    @property
    @instance_cache
    def messages(self):
        return [message.message
                for message in self._localized_messages]

    @property
    @instance_cache
    def exceptions(self):
        return list(filter(lambda e: e is not None,
                           (m.to_exception() for m in self._task_messages)))

    def has_exception(self):
        return len(self.exceptions) > 0


class UnityJobList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityJob


class UnityJobTask(UnityAttributeResource):
    pass


class UnityJobTaskList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityJobTask


class UnityMessage(UnityAttributeResource):
    def to_exception(self):
        if self.error_code != 0:
            clz = get_rest_exception(self.error_code)
            ret = clz(self)
        else:
            ret = None
        return ret

    def get_messages(self):
        return [m.message for m in self.messages]


class UnityMessageList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityMessage


class UnityLocalizedMessage(UnityAttributeResource):
    pass


class UnityLocalizedMessageList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityLocalizedMessage


def wait_job_completion(job, **kwargs):
    interval = kwargs.pop('interval', 5)
    timeout = kwargs.pop('timeout', 3600)

    @retryz.retry(timeout=timeout, wait=interval, on_return=False)
    def _do_update():
        job.update()
        if job.state == enums.JobStateEnum.COMPLETED:
            return True
        elif job.state in (enums.JobStateEnum.FAILED,
                           enums.JobStateEnum.ROLLING_BACK,
                           enums.JobStateEnum.COMPLETED_WITH_ERROR):
            raise ex.JobStateError(job)
        return False

    try:
        _do_update()
    except retryz.RetryTimeoutError:
        raise ex.JobTimeoutException()
