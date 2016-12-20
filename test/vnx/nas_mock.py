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

import six
import xmltodict as xmltodict
import xml.etree.ElementTree as ET
from mock import patch

from storops.lib.common import cache, allow_omit_parentheses
from storops.vnx.nas_client import VNXNasClient
from storops.vnx.xmlapi import XML_NS
from test.utils import ConnectorMock, read_test_file
from test.vnx.cli_mock import MockCli

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


ET.register_namespace('', XML_NS)


@cache
def t_nas():
    """ get the test NAS client

    :return: test NAS client
    """
    return VNXNasClient("10.110.24.191", 'nasadmin', 'nasadmin')


class MockXmlPost(ConnectorMock):
    base_folder = os.path.join('vnx', 'testdata', 'nas_xml_output')

    @classmethod
    def get_folder(cls, body):
        skipped_nodes = ('RequestPacket', 'Request')

        ret = [cls.base_folder]
        # get two levels after Request
        node = ET.fromstring(body.encode('utf-8'))
        while len(ret) < 3:
            tag = cls.delete_ns(node.tag)
            if tag in skipped_nodes:
                pass
            else:
                ret.append(tag)
            children = node.getchildren()
            if not children:
                break
            node = children[0]
        return os.path.join(*ret)

    def mock_post(self, body):
        return self.get_mock_output(body)

    @staticmethod
    def delete_ns(tag):
        if '}' in tag:
            tag = tag[tag.index('}') + 1:]
        return tag

    @staticmethod
    @cache
    def read_index(folder):
        return read_test_file(folder, 'index.xml')

    @classmethod
    def get_filename(cls, body):
        xml_string = cls.read_index(cls.get_folder(body))
        indices = ET.fromstring(xml_string.encode('utf-8'))
        ret = None
        for index in indices:
            for request_packet in index:
                if xml_compare(request_packet, body):
                    if 'output' not in index.attrib:
                        raise AttributeError(
                            'missing "output" attribute in "Index" node.')
                    ret = index.attrib['output']
                    break
            if ret:
                break
        else:
            log.error('cannot find response for request: \n{}'.format(body))

        return ret


@allow_omit_parentheses
def patch_post(output=None, mock_map=None):
    xml = MockXmlPost(output, mock_map)

    def decorator(func):
        @functools.wraps(func)
        @patch(target='storops.connection.connector.XMLAPIConnector.post',
               new=xml.mock_post)
        @patch(target='storops.connection.connector.XMLAPIConnector._login',
               new=lambda a, b, c, d: 0)
        @patch(target='storops.lib.common.const_seconds',
               new=lambda x: 0)
        def func_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return func_wrapper

    return decorator


class MockSsh(MockCli):
    base_folder = os.path.join('vnx', 'testdata', 'ssh_output')

    flags_to_delete = {'NAS_DB=/nas': 1}

    def mock_execute(self, command, timeout=None, check_exit_code=True):
        if len(command) > 2:
            folder = '/nas/bin/'
            if folder in command[2]:
                command[2] = command[2].replace(folder, '')
        return self.get_mock_output(command), None

    def mock_init_connection(self, *args):
        pass


def patch_ssh(output=None, mock_map=None):
    ssh = MockSsh(output, mock_map)

    def decorator(func):
        @functools.wraps(func)
        @patch(target='storops.connection.connector.SSHConnector.execute',
               new=ssh.mock_execute)
        @patch(target='storops.connection.connector.SSHConnector.'
                      'init_connection',
               new=ssh.mock_init_connection)
        def func_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return func_wrapper

    return decorator


@allow_omit_parentheses
def patch_nas(xml_output=None, xml_map=None, ssh_output=None, ssh_map=None):
    xml = MockXmlPost(xml_output, xml_map)
    ssh = MockSsh(ssh_output, ssh_map)

    def decorator(func):
        @functools.wraps(func)
        @patch(target='storops.connection.connector.XMLAPIConnector.post',
               new=xml.mock_post)
        @patch(target='storops.connection.connector.XMLAPIConnector._login',
               new=lambda a, b, c, d: 0)
        @patch(target='storops.lib.common.const_seconds',
               new=lambda x: 0)
        @patch(target='storops.connection.connector.SSHConnector.execute',
               new=ssh.mock_execute)
        @patch(target='storops.connection.connector.SSHConnector.'
                      'init_connection',
               new=ssh.mock_init_connection)
        def func_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return func_wrapper

    return decorator


def normalise_dict(d):
    """ Recursively convert dict-like object (eg OrderedDict) into plain dict.

    And sorts list values.
    :param d: dict input
    """
    out = {}
    for k, v in d.items():
        if hasattr(v, 'items'):
            out[k] = normalise_dict(v)
        elif isinstance(v, list):
            out[k] = []
            for item in sorted(v):
                if hasattr(item, 'items'):
                    out[k].append(normalise_dict(item))
                else:
                    out[k].append(item)
        else:
            out[k] = v
    return out


def xml_compare(a, b):
    """ Compares two XML documents (as string or etree)

    Does not care about element order
    :param a: xml to compare
    :param b: xml to compare
    """
    if not isinstance(a, six.string_types):
        a = ET.tostring(a, encoding='utf-8').decode('utf-8')
    if not isinstance(b, six.string_types):
        b = ET.tostring(b, encoding='utf-8').decode('utf-8')
    a = normalise_dict(xmltodict.parse(a))
    b = normalise_dict(xmltodict.parse(b))
    return a == b
