# coding=utf-8
# Copyright (c) 2020 Dell Inc. or its subsidiaries.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from __future__ import unicode_literals

import persistqueue


class SGCache(persistqueue.PDict):
    """SGCache shares the VNX SG caching between OpenStack Cinder backends.

    This shared cache is introduced to fix the issue like:
    https://github.com/emc-openstack/storops/issues/305. The fix to storops is
    not enough though. Because different OpenStack VNX Cinder backends for
    two or more pools will have the dirty cache as described in issue #305.

    The shared cache will persist the VNX storage groups information in the
    same file path on the same machine via ``persistqueue.PDict``.
    """

    def __init__(self, persist_path):
        self._persist_path = persist_path
        super(SGCache, self).__init__(persist_path, 'storops_sg_cache',
                                      multithreading=True)
