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

import storops.vnx.resource.lun
from storops.lib.common import instance_cache
from storops.vnx.resource import VNXCliResourceList, VNXCliResource

__author__ = 'Cedric Zhuang'


class VNXMigrationSessionList(VNXCliResourceList):
    @classmethod
    def get_resource_class(cls):
        return VNXMigrationSession

    def _get_raw_resource(self):
        return self._cli.get_migration_session(poll=self.poll)


class VNXMigrationSession(VNXCliResource):
    def __init__(self, source=None, cli=None):
        super(VNXMigrationSession, self).__init__()
        self._cli = cli
        self._source = source

    def _get_raw_resource(self):
        source_id = storops.vnx.resource.lun.VNXLun.get_id(self._source)
        return self._cli.get_migration_session(source_id, poll=self.poll)

    @property
    def is_migrating(self):
        return self.current_state == 'MIGRATING'

    @property
    def is_success(self):
        return self.current_state in ('MIGRATED', None)

    @classmethod
    def get(cls, cli, source=None):
        if source is None:
            ret = VNXMigrationSessionList(cli)
        else:
            ret = VNXMigrationSession(source, cli)
        return ret

    @property
    @instance_cache
    def source_lun(self):
        if self._source is not None:
            return storops.vnx.resource.lun.VNXLun(
                lun_id=self._source,
                cli=self._cli)
        return storops.vnx.resource.lun.VNXLun.get(
            cli=self._cli, lun_id=self.source_lu_id, name=self.source_lu_name)

    @property
    @instance_cache
    def destination_lun(self):
        return storops.vnx.resource.lun.VNXLun.get(
            cli=self._cli, lun_id=self.dest_lu_id, name=self.dest_lu_name)

    def cancel(self):
        self.source_lun.cancel_migrate()
