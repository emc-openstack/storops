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

from storops_comptest.unity import UnityGeneralFixture, UnityCifsShareFixture
from storops_comptest.utils import is_jenkins, setup_fixture

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def unity_gf(request):
    """ General fixture for most unity cases

    :param request:
    :return:
    """
    return setup_fixture(request, UnityGeneralFixture)


@pytest.fixture(scope="session", autouse=True)
def unity_cs(request):
    """ General fixture for unity cifs share in domain

    :param request:
    :return:
    """
    if is_jenkins():
        pytest.skip('do not run on CI, manual only.')

    return setup_fixture(request, UnityCifsShareFixture)
