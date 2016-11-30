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

import functools
import logging
import os
import re
from datetime import timedelta

import six
from mock import patch

from storops import VNXSPEnum
from storops.lib.common import cache, allow_omit_parentheses
from storops.lib.resource import ResourceListCollection
from storops.vnx.block_cli import CliClient
from storops.vnx.resource.disk import VNXDiskList
from storops.vnx.resource.lun import VNXLunList
from storops.vnx.resource.port import VNXSPPortList
from storops.vnx.resource.system import VNXSystem
from storops.vnx.resource.vnx_domain import VNXStorageProcessor, \
    VNXStorageProcessorList
from test.utils import ConnectorMock

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


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
        def func_wrapper(*args):
            return func(*args)

        return func_wrapper

    return decorator


def extract_command(func):
    """patch `CliClient.execute` method for unittest

    Patch `CliClient.execute` to return the parameters.
    The command line parameter can be verified by unittest.

    :param func: test function to wrap
    """

    def mock(_, commands, ip=None):
        if ip is None:
            pre = ''
        else:
            pre = '[{}] '.format(ip)
        return pre + ' '.join(map(six.text_type, commands))

    @functools.wraps(func)
    @patch(target='storops.vnx.block_cli.CliClient.execute', new=mock)
    @patch(target='storops.vnx.block_cli.CliClient.execute_dual', new=mock)
    def func_wrapper(self):
        return func(self)

    return func_wrapper


@cache
@patch_cli
def t_cli(version=None):
    """ get the test cli client

    :param with_stats: if true, returns a client with stats enabled.
    :param version: system version
    :return: test cli client
    """
    c = CliClient('10.244.212.182', heartbeat_interval=0)
    c.set_system_version(version)
    c.get_agent()
    prev = ResourceListCollection([get_sp_list_t0(c),
                                   get_lun_list_t0(c),
                                   get_disk_list_t0(c),
                                   get_port_list_t0(c)])
    curr = ResourceListCollection([get_sp_list_t1(c),
                                   get_lun_list_t1(c),
                                   get_disk_list_t1(c),
                                   get_port_list_t1(c)])
    curr.timestamp += timedelta(seconds=60)
    c.add_metric_record(prev)
    c.add_metric_record(curr)
    return c


@cache
def t_vnx():
    """ get the test vnx instance

    :return: test vnx instance
    """
    return VNXSystem('10.244.211.30', heartbeat_interval=0,
                     file_username='nasadmin',
                     file_password='nasadmin')


@patch_cli
def get_sp_list_t0(cli):
    sp = VNXStorageProcessor(cli, VNXSPEnum.SP_A, '10.244.211.30')
    sp.with_no_poll()
    ret = VNXStorageProcessorList(sp)
    ret.update()
    return ret


@patch_cli
def get_sp_list_t1(cli):
    sp = VNXStorageProcessor(cli, VNXSPEnum.SP_A, '10.244.211.30')
    ret = VNXStorageProcessorList(sp)
    ret.update()
    return ret


@patch_cli(output='lun_-list_-all_t0.txt')
def get_lun_list_t0(cli):
    return VNXLunList(cli=cli).update()


@patch_cli(output='getdisk_t0.txt')
def get_disk_list_t0(cli):
    return VNXDiskList(cli=cli).update()


@patch_cli(output='lun_-list_-all_t1.txt')
def get_lun_list_t1(cli):
    return VNXLunList(cli=cli).update()


@patch_cli(output='getdisk_t1.txt')
def get_disk_list_t1(cli):
    return VNXDiskList(cli=cli).update()


@patch_cli
def get_port_list_t0(cli):
    return VNXSPPortList(cli=cli).update()


@patch_cli(output='port_-list_-sp_-all_t1.txt')
def get_port_list_t1(cli):
    return VNXSPPortList(cli=cli).update()
