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

from comptest.utils import inter_process_locked
from storops import VNXSystem, UnitySystem, cache

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


@inter_process_locked('t_vnx.lck')
@cache
def t_vnx():
    vnx = VNXSystem('10.244.211.30', 'sysadmin', 'sysadmin')
    log.debug('initialize vnx system: {}'.format(vnx))
    return vnx


@inter_process_locked('t_unity.lck')
@cache
def t_unity():
    unity = UnitySystem('10.244.223.61', 'admin', 'Password123!')
    log.debug('initialize unity system: {}'.format(unity))
    return unity


@inter_process_locked('t_vnx.lck')
@cache
def vnx1():
    vnx = VNXSystem('192.168.1.52', 'sysadmin', 'sysadmin')
    log.debug('initialize vnx system: {}'.format(vnx))
    return vnx


@inter_process_locked('t_vnx.lck')
@cache
def vnx2():
    vnx = VNXSystem('192.168.1.94', 'sysadmin', 'sysadmin')
    log.debug('initialize vnx system: {}'.format(vnx))
    return vnx
