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
import re

import six
from retryz import retry

from storops.connection import connector
from storops.exception import VNXBackendError, VNXLockRequiredException, \
    VNXNasObjectNotFound, VNXInvalidMoverID, VNXException, \
    get_xmlapi_exception, VNXFileCredentialError
from storops.lib.common import Enum, check_int
from storops.lib.converter import to_int, to_hex
from storops.vnx.nas_cmd import NasCommand
from storops.vnx.resource.cifs_share import CifsAccessControl
from storops.vnx.xmlapi import NasXmlBuilder
from storops.vnx.xmlapi_parser import XMLAPIParser

__author__ = 'Jay Xu'

log = logging.getLogger(__name__)


class VNXNasConnections(object):
    retry_patterns = [(r'unable to acquire lock\(s\)',
                       VNXLockRequiredException())]

    def __init__(self, host, username, password, ssh_port=22):
        self.host = host
        self.username = username
        self.password = password
        self.ssh_port = ssh_port

        self._ssh_timeout = None

        self._ssh = None
        self._xml_connector = None
        self._xml_parser = None

    @property
    def ssh(self):
        if self._ssh is None:
            self._ssh = self._ssh = connector.SSHConnector(
                self.host, self.username, self.password, self.ssh_port)
        return self._ssh

    def set_ssh_timeout(self, value):
        self._ssh_timeout = check_int(value)

    @property
    def xml_connector(self):
        if self._xml_connector is None:
            self._xml_connector = connector.XMLAPIConnector(
                self.host, self.username, self.password)
        return self._xml_connector

    @property
    def xml_parser(self):
        if self._xml_parser is None:
            self._xml_parser = XMLAPIParser()
        return self._xml_parser

    @classmethod
    def _get_req_xml(cls, req):
        base = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>{}'
        return base.format(req)

    @retry(on_error=VNXLockRequiredException)
    def _request(self, req, retry_patterns=None):

        req_xml = self._get_req_xml(req)
        log.debug('request: \n{}'.format(req_xml))

        rsp_xml = self.xml_connector.post(req_xml)

        if isinstance(rsp_xml, tuple):
            rsp_xml = rsp_xml[1]
        log.debug('response: \n{}'.format(rsp_xml))

        response = NasXmlResponse(self.xml_parser.parse(rsp_xml))

        if not retry_patterns:
            retry_patterns = self.retry_patterns
        if response.is_error():
            for pattern in retry_patterns:
                messages = response.problem_messages
                to_match, to_raise = pattern
                if re.search(to_match, messages):
                    raise to_raise

        return response

    def request(self, req, check_object=False, check_invalid_data_mover=False,
                error_desc=None, retry_patterns=None):
        response = self._request(req, retry_patterns)

        if check_object:
            response.raise_if_no_object(error_desc)

        if check_invalid_data_mover:
            response.check_invalid_data_mover()

        return response

    def ssh_execute(self, commands, check_exit_code=True):
        out, _ = self.ssh.execute(commands, self._ssh_timeout, check_exit_code)
        return out


def xml_request(check_object=False, check_invalid_data_mover=False):
    """ indicate the return value is a xml api request

    :param check_invalid_data_mover:
    :param check_object:
    :return: the response of this request
    """

    def decorator(f):
        @functools.wraps(f)
        def func_wrapper(self, *argv, **kwargs):
            request = f(self, *argv, **kwargs)
            return self.request(
                request, check_object=check_object,
                check_invalid_data_mover=check_invalid_data_mover)

        return func_wrapper

    return decorator


xml_get_request = xml_request()
xml_set_request = xml_request(check_invalid_data_mover=True)


def nas_command(f):
    """ indicate it's a command of nas command run with ssh

    :param f: function that returns the command in list
    :return: command execution result
    """

    @functools.wraps(f)
    def func_wrapper(self, *argv, **kwargs):
        commands = f(self, *argv, **kwargs)
        return self.ssh_execute(['env', 'NAS_DB=/nas'] + commands)

    return func_wrapper


class VNXNasClient(VNXNasConnections):
    @xml_get_request
    def get_filesystem(self, name=None, fs_id=None):
        return NasXmlBuilder.get_filesystem(name, fs_id=fs_id)

    @xml_set_request
    def create_filesystem(self, name, size, pool_id,
                          mover_id, is_vdm=False):
        return NasXmlBuilder.create_filesystem(
            name, size, pool_id, mover_id, is_vdm)

    @xml_set_request
    def delete_filesystem(self, fs_id):
        return NasXmlBuilder.delete_filesystem(fs_id)

    @xml_set_request
    def extend_fs(self, fs_id, delta_size, pool_id):
        return NasXmlBuilder.extend_filesystem(fs_id, delta_size, pool_id)

    @xml_get_request
    def get_nas_pool(self):
        return NasXmlBuilder.get_nas_pool()

    @xml_get_request
    def get_mover(self, mover_id=None, full=True):
        return NasXmlBuilder.get_mover(mover_id, full)

    @xml_set_request
    def create_dns_domain(self, mover_id, domain_name, servers,
                          protocol='udp'):
        return NasXmlBuilder.create_dns_domain(
            mover_id, domain_name, servers, protocol)

    @xml_set_request
    def delete_dns_domain(self, mover_id, domain_name):
        return NasXmlBuilder.delete_dns_domain(mover_id, domain_name)

    @xml_get_request
    def get_fs_snap(self, name=None, snap_id=None):
        return NasXmlBuilder.get_fs_snap(name, snap_id)

    @xml_set_request
    def create_snap(self, name, fs_id, pool_id, size=None):
        return NasXmlBuilder.create_snap(name, fs_id, pool_id, size)

    @xml_set_request
    def delete_snap(self, snap_id, force=False):
        return NasXmlBuilder.delete_snap(snap_id, force)

    @xml_get_request
    def get_cifs_server(self, name=None, mover_id=None, is_vdm=False):
        return NasXmlBuilder.get_cifs_server(name, mover_id, is_vdm)

    @xml_set_request
    def create_cifs_server(self, name,
                           mover_id, is_vdm=False,
                           workgroup=None, domain=None,
                           ip_list=None,
                           alias_name=None,
                           local_admin_password=None):
        return NasXmlBuilder.create_cifs_server(
            name=name, mover_id=mover_id, is_vdm=is_vdm,
            workgroup=workgroup, domain=domain,
            ip_list=ip_list, alias_name=alias_name,
            local_admin_password=local_admin_password)

    @xml_get_request
    def modify_domain_cifs_server(self, name, mover_id, is_vdm=False,
                                  join_domain=None, username=None,
                                  password=None):
        return NasXmlBuilder.modify_domain_cifs_server(
            name, mover_id, is_vdm, join_domain, username, password)

    @xml_set_request
    def delete_cifs_server(self, name, mover_id=None, is_vdm=False):
        return NasXmlBuilder.delete_cifs_server(name, mover_id, is_vdm)

    @xml_get_request
    def get_fs_mp(self, path=None, mover_id=None, is_vdm=False):
        return NasXmlBuilder.get_fs_mp(path, mover_id, is_vdm)

    @xml_set_request
    def create_fs_mp(self, path, fs_id, mover_id, is_vdm=False):
        return NasXmlBuilder.create_fs_mp(path, fs_id, mover_id, is_vdm)

    @xml_set_request
    def delete_fs_mp(self, path, mover_id, is_vdm=False):
        return NasXmlBuilder.delete_fs_mp(path, mover_id, is_vdm)

    @xml_get_request
    def get_mover_host(self, mover_host_id=None):
        return NasXmlBuilder.get_mover_host(mover_host_id)

    @xml_set_request
    def create_mover_interface(self, mover_id, device, ip, net_mask,
                               vlan_id=0, name=None):
        return NasXmlBuilder.create_mover_interface(
            mover_id, device, ip, net_mask, vlan_id, name)

    @xml_set_request
    def delete_mover_interface(self, mover_id, ip):
        return NasXmlBuilder.delete_mover_interface(mover_id, ip)

    @nas_command
    def get_mover_interconnect_id_list(self):
        return NasCommand.nas_cel_list()

    @xml_get_request
    def get_vdm(self, vdm_id=None):
        return NasXmlBuilder.get_vdm(vdm_id)

    @xml_set_request
    def create_vdm(self, mover_id, name, pool_id=None):
        return NasXmlBuilder.create_vdm(mover_id, name, pool_id)

    @xml_set_request
    def delete_vdm(self, vdm_id):
        return NasXmlBuilder.delete_vdm(vdm_id)

    @nas_command
    def get_dm_interfaces(self, name=None, is_vdm=True):
        return NasCommand.get_dm_interfaces(name, is_vdm)

    @nas_command
    def attach_nfs_interface(self, if_name, vdm_name=None):
        return NasCommand.attach_nfs_interface(if_name=if_name,
                                               vdm_name=vdm_name)

    @nas_command
    def detach_nfs_interface(self, if_name, vdm_name=None):
        return NasCommand.detach_nfs_interface(if_name=if_name,
                                               vdm_name=vdm_name)

    @xml_get_request
    def get_nfs_export(self, mover_id=None, path=None):
        return NasXmlBuilder.get_nfs_export(mover_id, path)

    @xml_set_request
    def create_nfs_export(self, mover_id, path, ro=False, host_config=None):
        return NasXmlBuilder.create_nfs_export(mover_id, path, ro,
                                               host_config)

    @xml_set_request
    def delete_nfs_export(self, mover_id, path):
        return NasXmlBuilder.delete_nfs_export(mover_id, path)

    @xml_set_request
    def modify_nfs_export(self, mover_id, path, ro=None, host_config=None):
        return NasXmlBuilder.modify_nfs_export(mover_id, path, ro,
                                               host_config)

    @xml_get_request
    def get_cifs_share(self, server_name=None, share_name=None,
                       mover_id=None, is_vdm=False):
        return NasXmlBuilder.get_cifs_share(
            server_name, share_name, mover_id, is_vdm)

    @xml_set_request
    def create_cifs_share(self, name, server_name, mover_id,
                          is_vdm=False, path=None):
        return NasXmlBuilder.create_cifs_share(name, server_name, mover_id,
                                               is_vdm, path)

    @xml_set_request
    def delete_cifs_share(self, name, mover_id, server_names, is_vdm=False):
        return NasXmlBuilder.delete_cifs_share(
            name=name, mover_id=mover_id, server_names=server_names,
            is_vdm=is_vdm)

    @nas_command
    def disable_cifs_share_access(self, share_name, mover_name):
        return NasCommand.disable_cifs_share_access(share_name, mover_name)

    @nas_command
    def allow_cifs_share_access(self, share_name, mover_name, user_name,
                                domain, access=CifsAccessControl.FULL):
        return NasCommand.allow_cifs_share_access(
            share_name, mover_name, user_name, domain, access)

    @nas_command
    def deny_cifs_share_access(self, share_name, mover_name, user_name,
                               domain, access=CifsAccessControl.FULL):
        return NasCommand.deny_cifs_share_access(
            share_name, mover_name, user_name, domain, access)


class XmlStatus(Enum):
    OK = 'ok'
    INFO = 'info'
    DEBUG = 'debug'
    WARNING = 'warning'
    ERROR = 'error'


class NasXmlResponse(object):
    def __init__(self, resp, parser=None):
        self._check_credential_error(resp)
        resp = self._parse_resp(parser, resp)
        self._dict = resp

    @staticmethod
    def _check_credential_error(resp):
        if 'Session timeout. Relogin and try this operation again.' in resp:
            raise VNXFileCredentialError()

    @staticmethod
    def _parse_resp(parser, resp):
        if parser is None:
            parser = XMLAPIParser()
        if isinstance(resp, six.string_types):
            resp = parser.parse(resp)
        return resp

    @property
    def status(self):
        return XmlStatus.parse(self._dict['maxSeverity'])

    @status.setter
    def status(self, value):
        self._dict['maxSeverity'] = value

    @property
    def problems(self):
        return self._dict['problems']

    @property
    def objects(self):
        return self._dict['objects']

    def filter_object(self, **kwargs):
        objects = self.objects
        for k, v in kwargs.items():
            if v is not None:
                v = str(v)
                objects = list(filter(lambda obj: obj[k] == v, objects))
        self._dict['objects'] = objects

    @property
    def first_object(self):
        if len(self.objects) < 1:
            raise ValueError('not a single object available.')
        return self.objects[0]

    @property
    def problem_message_codes(self):
        return set(map(int, self._get_problem_props('messageCode')))

    @property
    def hex_problem_message_codes(self):
        ret = self.problem_message_codes
        return set(map(to_hex, ret))

    @property
    def problem_messages(self):
        return '\n'.join(set(self._get_problem_props('message')))

    @property
    def problem_diagnostics(self):
        return '\n'.join(set(self._get_problem_props('Diagnostics')))

    def _get_problem_props(self, key):
        return [problem[key] for problem in self.problems
                if key in problem]

    def get_status_msg(self, desc=None):
        msg = ('status: {}.\n'
               'problem details: \n'
               '{}'
               .format(self.status,
                       self.get_problems_string(' ' * 4)))
        if desc is not None:
            msg = '  '.join([desc, msg])
        return msg

    def get_problems_string(self, prefix=''):
        msgs = []
        for i, v in enumerate(self.problems, 1):
            msgs.append('{p}({i}) code: {mc}\n'
                        '{p}    message: {msg}\n'
                        '{p}    diagnostics: {d}\n'
                        .format(p=prefix, i=i,
                                mc=v['messageCode'],
                                msg=v['message'],
                                d=v.get('Diagnostics', 'N/A')))
        return ''.join(msgs)

    def check_invalid_data_mover(self):
        if not self.is_ok():
            try:
                self.raise_if_err()
            except VNXInvalidMoverID:
                raise
            except VNXException:
                # pass to upper level for further process
                pass

    def raise_if_err(self, desc=None):
        if not self.is_ok():
            msg = self.get_status_msg(desc)
            exception_clz = get_xmlapi_exception(
                self.problem_message_codes, default=VNXBackendError)
            raise exception_clz(message=msg)

    def raise_if_no_object(self, desc=None):
        if not self.objects:
            msg = self.get_status_msg(desc)
            raise VNXNasObjectNotFound(err=msg)

    def is_ok(self):
        return self.status in (XmlStatus.DEBUG, XmlStatus.INFO, XmlStatus.OK)

    def is_error(self):
        return self.status == XmlStatus.ERROR

    def has_error_code(self, code):
        return to_int(code) in self.problem_message_codes
