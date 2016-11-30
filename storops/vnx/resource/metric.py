# coding=utf-8
# Copyright (c) 2016 EMC Corporation.
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

from storops.exception import raise_if_err, VNXStatsException
from storops.vnx.resource import VNXCliResource

__author__ = 'Cedric Zhuang'


class VNXStats(VNXCliResource):
    def __init__(self, cli=None):
        super(VNXStats, self).__init__()
        self._cli = cli

    @classmethod
    def get(cls, cli):
        return VNXStats(cli=cli)

    def is_enabled(self):
        out = self._cli.set_stats()
        if 'ENABLED' in out:
            ret = True
        elif 'DISABLED' in out:
            ret = False
        else:
            raise VNXStatsException(out)
        return ret

    def enable_stats(self):
        out = self._cli.set_stats(True)
        raise_if_err(out, VNXStatsException)

    def disable_stats(self):
        out = self._cli.set_stats(False)
        raise_if_err(out, VNXStatsException)
