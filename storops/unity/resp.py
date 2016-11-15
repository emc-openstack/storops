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

from storops.exception import get_rest_exception
from storops.unity.resource import health
from storops.unity.resource import job
from storops.lib.common import instance_cache

__author__ = 'Cedric Zhuang'


class RestResponse(object):
    def __init__(self, inputs, cli=None):
        if isinstance(inputs, (tuple, list)):
            if len(inputs) == 2:
                self.response = inputs[0]
                self.body = inputs[1]
            elif len(inputs) == 1:
                self.response = None
                self.body = inputs[0]
            else:
                raise ValueError('not valid input: {}'.format(inputs))
        else:
            self.response = None
            self.body = inputs
        if not self.body:
            self.body = {}
        self._cli = cli

    @property
    def contents(self):
        if 'entries' in self.body:
            ret = [entry.get('content', {})
                   for entry in self.body['entries']]
        elif 'content' in self.body:
            ret = [self.body.get('content')]
        else:
            ret = []
        return ret

    @property
    def entries(self):
        return self.body.get('entries', [])

    @property
    def first_content(self):
        contents = self.contents
        if contents:
            ret = contents[0]
        else:
            ret = {}
        return ret

    @property
    def resource_id(self):
        ret = self.first_content.get('id')
        if ret is None:
            sr = self.first_content.get('storageResource')
            if sr is not None:
                ret = sr.get('id')
        return ret

    def has_error(self):
        return self.error is not None

    def is_ok(self):
        return not self.has_error()

    @property
    def has_next_page(self):
        return self.next_page is not None

    @property
    def next_page(self):
        return self._get_page_number('next')

    @property
    def current_page(self):
        return self._get_page_number('self')

    def _get_page_number(self, which_page):
        links = self.body.get('links')
        ret = None
        if links:
            page_link = list(filter(lambda l: l.get('rel') == which_page,
                                    links))
            if page_link:
                href = page_link[0].get('href')
                if href:
                    items = href.split('=')
                    if len(items) > 1:
                        ret = int(items[1])
        return ret

    @property
    @instance_cache
    def error(self):
        clz = health.UnityError
        err = self.body.get('error')
        if err is not None:
            ret = clz().update(err)
        else:
            ret = None
        return ret

    @property
    def error_code(self):
        if self.has_error():
            ret = self.error.error_code
        else:
            ret = None
        return ret

    def raise_if_err(self):
        if self.has_error():
            ex_clz = get_rest_exception(self.error_code)
            raise ex_clz(self.error)

    @property
    @instance_cache
    def job(self):
        ret = job.UnityJob(cli=self._cli)
        ret.update(self.body)
        return ret
