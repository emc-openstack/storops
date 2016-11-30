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
import os

import six
from subprocess import Popen, PIPE

import time

import storops.exception as ex
from storops.lib.common import int_var, text_var, synchronized, cache, daemon

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class NaviCommand(object):
    def __init__(self, username=None, password=None, scope=0,
                 sec_file=None, timeout=None, naviseccli=None):
        self._username = username
        self._password = password
        self._scope = scope
        self._sec_file = sec_file
        self._timeout = timeout
        self._customized_cli = naviseccli
        self._is_credential_valid = True

    MAX_TIMEOUT = 1800
    MIN_TIMEOUT = 3

    def set_credential(self, username=None, password=None, scope=None,
                       sec_file=None):
        if username is not None:
            self._username = username
        if password is not None:
            self._password = password
        if scope is not None:
            self._scope = scope
        if sec_file is not None:
            self._sec_file = sec_file
        self._is_credential_valid = True

    @property
    def timeout(self):
        ret = self._timeout
        if ret is not None:
            ret = int(ret)
            if ret > 1800:
                log.warning('timeout {0} is larger than {1}, reset to {1}.'
                            .format(ret, self.MAX_TIMEOUT))
                ret = 1800
            if ret < 3:
                log.warning('timeout {0} is less than {1}, reset to {1}.'
                            .format(ret, self.MIN_TIMEOUT))
                ret = 3
        return ret

    @property
    def is_credential_valid(self):
        return self._is_credential_valid

    def get_credentials(self):
        if self._sec_file:
            # use security file
            ret = text_var('-secfilepath', self._sec_file)
        elif self._username is None and self._password is None:
            ret = []
        elif self._username is None or self._password is None:
            self._is_credential_valid = False
            raise ex.VNXCredentialError('username or password missing.')
        else:
            ret = ['-user', self._username,
                   '-password', self._password,
                   '-scope', self._scope]
        if self.timeout is not None:
            ret += int_var('-t', self.timeout)
        return ret

    _cli_binary_candidates = (
        r'/opt/Navisphere/bin/naviseccli',
        r'C:\Program Files (x86)\EMC\Navisphere CLI\naviseccli.exe',
        r'C:\Program Files\EMC\Navisphere CLI\naviseccli.exe')

    def set_binary(self, binary):
        """ set the location of naviseccli binary

        :param binary: the absolute path of naviseccli
        :return: nothing
        """
        self._customized_cli = binary

    def _binary(self):
        if self._customized_cli is None:
            binary = 'naviseccli'
            for c in self._cli_binary_candidates:
                if os.path.exists(c):
                    binary = c
                    break
        else:
            binary = self._customized_cli
        self._init_security_level(binary)
        return binary

    def get_cmd_prefix(self, ip):
        binary = self._binary()
        return [binary, '-h', ip] + self.get_credentials()

    @classmethod
    def execute_naviseccli(cls, cmd):
        cmd = list(map(six.text_type, cmd))
        try:
            ret = cls.execute(cmd)
        except OSError:
            raise ex.NaviseccliNotAvailableError()
        return ret

    @classmethod
    def execute(cls, cmd, timeout=None):
        if timeout is None:
            timeout = cls.MAX_TIMEOUT
        # closure cannot modify value, use list to work around
        process = [None]
        output = [None]

        def run():
            start = time.time()
            cls._log_command(cmd)

            p = Popen(cmd, bufsize=-1, stdout=PIPE, stderr=PIPE)
            process[0] = p
            out = p.stdout.read()

            cls._log_output(cmd, out, start)
            if isinstance(out, bytes):
                out = out.decode("utf-8")
            out = out.strip()
            output[0] = out
            return out

        thread = daemon(run)
        thread.join(timeout)
        if thread.is_alive() and process[0] is not None:
            log.warn('terminate timeout command: {}'.format(cmd))
            process[0].terminate()
            thread.join()
        return output[0]

    @classmethod
    def _log_command(cls, cmd):
        log.info('call command: {}'.format(cls._get_cmd_str(cmd)))

    @classmethod
    def _get_cmd_str(cls, cmd):
        cmd_cpy = cmd[:]
        # shadow password
        if len(cmd_cpy) >= 7 and cmd_cpy[5] == '-password':
            cmd_cpy[6] = '***'
        cmd_str = ' '.join(cmd_cpy)
        return cmd_str

    @classmethod
    def _log_output(cls, cmd, output, start):
        if log.isEnabledFor(logging.DEBUG):
            output = six.text_type(output).replace('\r\n', '\n').strip()
            if not output:
                output = 'empty'
            else:
                output = '\n' + output

            dt = time.time() - start
            log.debug(
                'command complete: {}, time consumed (s): {}, '
                'output: {}'.format(cls._get_cmd_str(cmd), dt, output))

    @classmethod
    def get_security_level(cls, binary):
        cmd = 'security -certificate -getLevel'.split()
        cmd.insert(0, binary)
        return cls.execute_naviseccli(cmd).lower()

    @classmethod
    def set_security_level(cls, binary, level='low'):
        possible_security_level = ('low', 'high')
        if level not in possible_security_level:
            raise ValueError(
                'possible security level: {}'.format(
                    possible_security_level))
        cmd = 'security -certificate -setLevel {}'.format(level).split()
        cmd.insert(0, binary)
        cls.execute_naviseccli(cmd)

    @staticmethod
    @synchronized()
    @cache
    def _init_security_level(binary):
        # have to specify the specified class
        # otherwise cls could be different for different subclass
        # and cache won't work.
        cls = NaviCommand
        current_level = cls.get_security_level(binary)
        if current_level != 'low':
            log.warn('security level is "{}", update to "low".'.format(
                current_level))
            cls.set_security_level(binary, 'low')
