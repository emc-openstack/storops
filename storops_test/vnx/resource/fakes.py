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

import mock

__author__ = 'Jay Xu'

Ki = 1024

STORAGE_GROUP_HBA = """
HBA UID                                          SP Name  SPPort
-------                                          -------  ------
iqn.1991-05.com.microsoft:abc.def.dev             SP A     3
Host name:             abc.def.dev
SPPort:                A-3v1
Initiator IP:          10.244.209.72
TPGT:                  1
ISID:                  10000000000
"""

patch_retry = mock.patch(target='storops.lib.common.const_seconds',
                         new=lambda x: 0)
