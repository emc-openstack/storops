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

from storops import exception as ex
from storops.unity.resource.job import UnityJob


class MockJobHelper(object):
    def __init__(self, cli, interval=5):
        self._cli = cli
        self.started = True

    def wait_job(self, job, async_timeout, async_interval):
        if job.id == 'N-3078':
            return UnityJob(_id=job.id, cli=self._cli)
        if job.id == 'N-3079':
            ret_job = UnityJob(_id=job.id, cli=self._cli)
            raise ex.JobStateError(ret_job)
        if job.id == 'N-3080':
            raise ex.JobTimeoutException()
