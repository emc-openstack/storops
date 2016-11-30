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

import codecs
import json
import logging
import math
import os
from os.path import dirname, abspath, join, exists, basename

import fasteners
from hamcrest.core.base_matcher import BaseMatcher

from storops.lib.common import instance_cache, get_lock_file, get_data_file

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


def read_test_file(folder, name):
    p = dirname(abspath(__file__))
    p = join(p, folder)
    p = join(p, name)
    if not exists(p):
        log.warn('cannot find mock output file: %s, '
                 'default to empty string.', p)
        raise IOError('file: {} not found.'.format(p))
    else:
        with codecs.open(p, 'r', 'utf-8') as f:
            if basename(p) not in ('index.xml', 'index.json'):
                log.info('read mock file: %s', p)
            ret = f.read()

    return ret


class ConnectorMock(object):
    base_folder = ''

    def __init__(self, output=None, mock_map=None):
        self._output = output
        self._mock_map = mock_map

    @classmethod
    def read_file(cls, filename, *sub_folders):
        folder = join(cls.base_folder, *sub_folders)
        return read_test_file(folder, filename)

    def update_mock_output(self, output, mock_map):
        self._output = output
        self._mock_map = mock_map

    def get_file_in_mock_map(self, param):
        ret = None
        if self._mock_map is not None:
            for key in self._mock_map.keys():
                if param.startswith(key):
                    ret = self._mock_map[key]
                    break
        return ret

    def get_mock_output(self, inputs):
        filename = self.get_filename(inputs)
        folder = self.get_folder(inputs)
        from_map = self.get_file_in_mock_map(filename)
        if self._output is not None:
            filename = self._output
        elif from_map:
            filename = from_map

        return read_test_file(folder, filename)

    def get_filename(self, inputs):
        raise NotImplementedError('specify the inputs-filename mapping.')

    def get_folder(self, inputs):
        raise NotImplementedError('mock data folder not specified.')


class PersistedDict(object):
    def __init__(self, name=None, default=None, folder=None):
        if name is None:
            name = self.__hash__()
        self._name = name
        self._default = default

    @property
    def lock_file_name(self):
        return get_lock_file('{}.lck'.format(self._name))

    @property
    @instance_cache
    def data_file_name(self):
        return get_data_file('{}.json'.format(self._name))

    @property
    @instance_cache
    def lock(self):
        return fasteners.InterProcessLock(self.lock_file_name)

    @property
    def dict(self):
        if exists(self.data_file_name):
            with open(self.data_file_name) as f:
                try:
                    ret = json.load(f)
                except ValueError:
                    ret = {}
        else:
            ret = {}
        return ret

    def __setitem__(self, key, value):
        with self.lock:
            data = self.dict
            data[key] = value
            with open(self.data_file_name, 'w') as f:
                if log.isEnabledFor(level=logging.DEBUG):
                    s = json.dumps(data, indent=4, sort_keys=True)
                    log.debug('set dict: {}\n{}'
                              .format(self.data_file_name, s))
                json.dump(data, f, indent=4, sort_keys=True)

    def __getitem__(self, item):
        with self.lock:
            d = self.dict
            if item in d:
                ret = d[item]
            elif self._default:
                if callable(self._default):
                    ret = self._default()
                else:
                    ret = self._default
            else:
                ret = d[item]
        return ret

    def __len__(self):
        return len(self.dict)

    def clear(self):
        with self.lock:
            with open(self.data_file_name, 'w') as f:
                json.dump({}, f)

    def destroy(self):
        s = json.dumps(self.dict, indent=4, sort_keys=True)
        log.debug('destroy dict {}: \n{}'.format(self.data_file_name, s))
        if exists(self.data_file_name):
            os.remove(self.data_file_name)

    def clear_lock_file(self):
        if exists(self.lock_file_name):
            os.remove(self.lock_file_name)


class IsNaN(BaseMatcher):
    def __init__(self):
        self.value = None

    def _matches(self, value):
        self.value = value
        return math.isnan(value)

    def describe_to(self, description):
        description.append_text('"{}" should be NaN.'.format(self.value))


def is_nan():
    return IsNaN()
