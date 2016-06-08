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

import pytest

from comptest.unity import UnityGeneralFixture, UnityCifsShareFixture
from comptest.utils import is_jenkins
from storops.lib.common import inter_process_locked

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def unity_gf(request):
    """ General fixture for most unity cases

    :param request:
    :return:
    """

    @inter_process_locked('unity_gf.lck')
    def _setup():
        log.info('setup general fixture.')
        return UnityGeneralFixture()

    fixture = _setup()

    def fin():
        log.info('tear down general fixture.')
        if fixture:
            fixture.clean_up()

    request.addfinalizer(fin)
    return fixture


@pytest.fixture(scope="session", autouse=True)
def unity_cs(request):
    """ General fixture for unity cifs share in domain

    :param request:
    :return:
    """
    if is_jenkins():
        pytest.skip('do not run on CI, manual only.')

    @inter_process_locked('unity_cs.lck')
    def _setup():
        log.info('setup cifs share fixture.')
        return UnityCifsShareFixture()

    fixture = _setup()

    def fin():
        log.info('tear down cifs share fixture.')
        if fixture:
            fixture.clean_up()

    request.addfinalizer(fin)
    return fixture
