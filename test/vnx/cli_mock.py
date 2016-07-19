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

import logging

import functools
import os

import re
import six
from mock import patch

from test.utils import ConnectorMock
from storops.lib.common import cache, allow_omit_parentheses
from storops.vnx.block_cli import CliClient
from storops.vnx.resource.system import VNXSystem

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


@cache
def t_cli(version=None):
    """ get the test cli client

    :return: test cli client
    """
    cli = CliClient("10.244.211.30", heartbeat_interval=0)
    cli.set_system_version(version)
    return cli


@cache
def t_vnx():
    """ get the test vnx instance

    :return: test vnx instance
    """
    return VNXSystem('10.244.211.30', heartbeat_interval=0,
                     file_username='nasadmin',
                     file_password='nasadmin')


class MockCli(ConnectorMock):
    base_folder = os.path.join('vnx', 'testdata', 'block_output')

    def get_folder(self, inputs):
        return self.base_folder

    def mock_execute(self, params, *args, **_):
        return self.get_mock_output(params)

    escaped_pattern = re.compile(r"[\\/:]")

    flags_to_delete = {
        '-t': 2
    }

    @classmethod
    def get_filename(cls, params):
        def delete_flag(arr, flag, flag_length=1):
            if flag in arr:
                i = arr.index(flag)
                if i > 0:
                    arr = arr[0:i] + arr[i + flag_length:]
                else:
                    arr = arr[flag_length:]
            return arr

        def delete_cli_binary(p):
            return p[1:]

        def delete_confidential(p):
            if p[0] == '-h':
                p = p[2:]
            if p[0] == '-user':
                p = p[2:]
            if p[0] == '-password':
                p = p[2:]
            if p[0] == '-scope':
                p = p[2:]
            return p

        params = delete_cli_binary(params)
        params = delete_confidential(params)

        for k, v in cls.flags_to_delete.items():
            params = delete_flag(params, k, v)
        name = '_'.join(map(six.text_type, params))
        name = re.sub(cls.escaped_pattern, '_', name)
        if len(name) >= 200:
            name = name[:43] + '____' + name[-43:]
        return '{}.txt'.format(name)


@allow_omit_parentheses
def patch_cli(output=None, mock_map=None):
    cli = MockCli(output, mock_map)

    def decorator(func):
        @functools.wraps(func)
        @patch(target='storops.vnx.navi_command.'
                      'NaviCommand.execute_naviseccli',
               new=cli.mock_execute)
        def func_wrapper(self):
            return func(self)

        return func_wrapper

    return decorator


def extract_command(func):
    """patch `CliClient.execute` method for unittest

    Patch `CliClient.execute` to return the parameters.
    The command line parameter can be verified by unittest.

    :param func: test function to wrap
    """

    def mock(_, commands):
        return ' '.join(map(six.text_type, commands))

    @functools.wraps(func)
    @patch(target='storops.vnx.block_cli.CliClient.execute', new=mock)
    @patch(target='storops.vnx.block_cli.CliClient.execute_dual', new=mock)
    def func_wrapper(self):
        return func(self)

    return func_wrapper
