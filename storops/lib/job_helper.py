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

import logging
import threading
import time
from collections import OrderedDict

from storops.lib.common import singleton
from storops.unity.resource.job import UnityJobList, wait_job_completion

log = logging.getLogger(__name__)


@singleton
class JobHelper(object):
    def __init__(self, cli, interval=3):
        self._cli = cli
        self._interval = interval
        self.jobs = OrderedDict()
        self.started = False

    def add_job(self, job):
        if job.id not in self.jobs:
            self.jobs[job.id] = job

    def remove_job(self, job):
        if job.id in self.jobs:
            del self.jobs[job.id]

    def get_job(self, job):
        if job.id in self.jobs:
            return self.jobs[job.id]

    def wait_job(self, job, timeout=3600, interval=3):
        def update_func(job):
            return self.get_job(job)

        try:
            self.add_job(job)
            job = wait_job_completion(job, timeout=timeout, interval=interval,
                                      update_func=update_func)
            return job
        finally:
            self.remove_job(job)

    def _query_jobs(self):
        if len(self.jobs) > 0:
            filters = {'id': list(self.jobs.keys())}
            log.debug('Query jobs from Unity, filter: {}'.format(filters))
            jobs = UnityJobList.get(cli=self._cli, **filters)
            log.debug('Query result: {}.'.format(jobs))
            for job in jobs:
                if hasattr(job, 'id'):
                    self.jobs[job.id] = job

    def query_jobs(self):
        try:
            while True:
                self._query_jobs()
                time.sleep(self._interval)
        except Exception as err:
            log.exception(
                'Job helper (thread: {}) exited with exception: {}'.format(
                    self.t.name, str(err)))
            self.started = False
            raise err

    def start(self):
        if self.started:
            return

        self.t = threading.Thread(name='job-helper-daemon',
                                  target=self.query_jobs)
        self.t.setDaemon(True)
        self.t.start()
        log.info('Job helper (thread: {}) started.'.format(self.t.name))
        self.started = True


def get_job_helper(cli):
    jh = JobHelper(cli)
    if not jh.started:
        jh.start()
    return jh
