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
from time import time, sleep

import six
from datetime import datetime

from storops.lib.common import daemon, WeightedAverage
from storops.vnx.enums import VNXSPEnum
import storops.exception as ex
from storops.vnx.navi_command import NaviCommand

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class NodeInfo(object):
    def __init__(self, name, ip, available=None, working=False):
        """ constructor for `NodeInfo`.

        :param name: name of the node, could be `spa`, or `spb`
        :param ip: ip address of the node
        :param available: indicate whether this node is alive.
        :param working: indicate whether this node is executing command.
        :return:
        """
        self.name = VNXSPEnum.parse(name)
        self.ip = ip.strip('\'" ')
        if available is None:
            available = True
        self._available = available
        self.timestamp = None
        self.working = working
        self._latency = WeightedAverage()

    @property
    def available(self):
        return self._available

    @available.setter
    def available(self, available):
        self._available = available
        self.timestamp = datetime.now()

    def is_updated_within(self, seconds):
        current = datetime.now()
        if self.timestamp is None:
            ret = False
        else:
            delta = current - self.timestamp
            ret = delta.total_seconds() < seconds
        return ret

    @property
    def latency(self):
        return self._latency.value()

    @latency.setter
    def latency(self, value):
        self._latency.add(value)

    def __repr__(self):
        props_to_print = ['name', 'ip', 'available',
                          'working', 'latency', 'timestamp']
        info = ', '.join(['{}: {}'.format(p, getattr(self, p))
                          for p in props_to_print])
        return info

    def __str__(self):
        return self.__repr__()


class NodeInfoMap(object):
    def __init__(self):
        self._map = dict()

    def update(self, node):
        if not isinstance(node, NodeInfo):
            raise ValueError('input must be an instance of _NodeInfo.')
        self._map[node.name] = node

    def is_available(self, name):
        ret = False
        name = VNXSPEnum.parse(name)
        if name in self._map:
            ret = self._map[name].available
        return ret

    def nodes(self):
        return list(self._map.values())

    def update_by_ip(self, ip, available=None, working=None, latency=None):
        node = self.get_node_by_ip(ip)
        if node is not None:
            if available is not None:
                node.available = available
            if working is not None:
                node.working = working
            if latency is not None:
                node.latency = latency

    def get_node_by_ip(self, ip):
        ret = None
        for node in self.nodes():
            if node.ip == ip:
                ret = node
                break
        return ret

    def __repr__(self):
        ret = 'node count: {}, detail: \n'.format(len(self._map))
        ret += '\n'.join(map(six.text_type, self._map.values()))
        return ret

    def __str__(self):
        return self.__repr__()


class NodeHeartBeat(NaviCommand):
    def __init__(self, username=None, password=None, scope=0,
                 sec_file=None, interval=60, timeout=30, naviseccli=None):
        super(NodeHeartBeat, self).__init__(username, password, scope,
                                            sec_file=sec_file,
                                            timeout=timeout,
                                            naviseccli=naviseccli)
        self._node_map = NodeInfoMap()
        self._interval = interval
        self._heartbeat_thread = None
        if interval > 0:
            self._heartbeat_thread = daemon(self._run)
        self.command_count = 0

    def reset(self):
        self._node_map = NodeInfoMap()
        self.command_count = 0

    def _get_sp_by_category(self):
        available_sp = []
        unavailable_sp = []
        nodes = self._node_map.nodes()
        for node in nodes:
            if VNXSPEnum.is_sp(node.name):
                if node.available:
                    available_sp.append(node)
                else:
                    unavailable_sp.append(node)
        return available_sp, unavailable_sp

    def get_alive_sp_ip(self):
        def get_sp_from_list(sp_list):
            ips = [sp.ip for sp in sp_list]
            return sorted(ips)[0]

        available, unavailable = self._get_sp_by_category()
        if len(available) == 0:
            raise ex.VNXSystemDownError(
                'no storage processor available.')
        else:
            ret = get_sp_from_list(available)
        return ret

    def is_all_sps_alive(self):
        _, unavailable = self._get_sp_by_category()
        return len(unavailable) == 0

    def get_all_alive_sps_ip(self):
        available, _ = self._get_sp_by_category()
        return [node.ip for node in available]

    def heart_beat(self):
        list(map(self._ping_node, self.nodes))

    @property
    def interval(self):
        return self._interval

    def _run(self):
        while self.interval > 0 and self.is_credential_valid:
            self.heart_beat()
            sleep(self.interval)
        self._heartbeat_thread = None

    def stop(self):
        if self.interval:
            log.info('exiting heart beat.')
            self.interval = 0

    def __del__(self):
        self.stop()

    @property
    def nodes(self):
        return self._node_map.nodes()

    @interval.setter
    def interval(self, value):
        self._interval = value
        if self._heartbeat_thread is None:
            # there is no loop check
            self._heartbeat_thread = daemon(self._run)

    def execute_cmd(self, ip, cmd):
        self.update_by_ip(ip, working=True)
        start = time()
        if not self.is_credential_valid:
            raise ex.VNXCredentialError(
                'cannot authenticate with user {}.'.format(self._username))
        out = self.execute_naviseccli(cmd)
        try:
            ex.check_error(out,
                           ex.VNXSpNotAvailableError,
                           ex.VNXCredentialError,
                           ex.VNXDropConnectionError)
            available = True
            latency = time() - start
        except ex.VNXSpNotAvailableError:
            log.exception('{} is not available.  detail: {}'.format(ip, out))
            available = False
            latency = None
        except ex.VNXCredentialError:
            self._is_credential_valid = False
            raise

        self.update_by_ip(ip, available, False, latency)
        self.command_count += 1

        if latency is None:
            msg = '{} is not available.'.format(ip)
            log.warn(msg)
            raise ex.VNXSPDownError(msg)
        return out

    def _ping_sp(self, ip):
        try:
            node = self._node_map.get_node_by_ip(ip)
            if node and not node.is_updated_within(self.interval):
                self.execute_cmd(ip, self.get_agent(ip))
        except OSError:
            log.debug('skip heartbeat, naviseccli not available.')
        except ex.VNXSPDownError:
            pass

    def get_agent(self, ip):
        cmd = self.get_cmd_prefix(ip)
        timeout = self.timeout
        if timeout is not None:
            latency = self.get_latency(ip)
            if latency is not None:
                timeout += latency
            if '-t' in cmd:
                index = cmd.index('-t') + 1
                cmd[index] = str(int(timeout))
        cmd += ['-np', 'getagent']
        return cmd

    def _ping_node(self, node):
        def do():
            self._ping_sp(node.ip)

        if VNXSPEnum.is_sp(node.name) and not node.working:
            daemon(do)

    def is_available(self, name):
        return self._node_map.is_available(name)

    def add(self, name, ip, available=None, working=False):
        if name is not None and ip is not None:
            node = NodeInfo(name, ip, available, working)
            self._node_map.update(node)

    def update_by_ip(self, ip, available=None, working=None, latency=None):
        self._node_map.update_by_ip(ip, available, working, latency)

    def get_latency(self, ip):
        node = self.get_node_by_ip(ip)
        ret = None
        if node is not None:
            ret = node.latency
        return ret

    def get_node_by_ip(self, ip):
        return self._node_map.get_node_by_ip(ip)

    def __repr__(self):
        return ('check interval: {}(seconds), total check count: {}, '
                'command timeout: {}(seconds), {}'
                .format(self.interval, self.command_count, self.timeout,
                        self._node_map))

    def __str__(self):
        return self.__repr__()

    # `__getstate__` and `__setstate__` are used by Pickle.
    # Because `_heartbeat_thread` is unpicklable, need to construct it
    # manually.
    def __getstate__(self):
        state = vars(self).copy()
        del state['_heartbeat_thread']
        return state

    def __setstate__(self, state):
        vars(self).update(state)
        if self.interval > 0:
            self._heartbeat_thread = daemon(self._run)
