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

from storops.vnx.resource import VNXCliResource, VNXCliResourceList
from storops import exception as ex
from storops.lib.common import round_3
from storops.lib.converter import block_to_gb

__author__ = 'Cedric Zhuang'


class VNXRaidGroup(VNXCliResource):
    def __init__(self, raid_group_id=None, cli=None):
        super(VNXRaidGroup, self).__init__()
        self._cli = cli
        self._raid_group_id = raid_group_id

    def _get_raid_group_id(self):
        if self._raid_group_id is not None:
            ret = self._raid_group_id
        else:
            ret = self.raid_group_id
        return ret

    def _get_raw_resource(self):
        return self._cli.get_rg(rg_id=self._raid_group_id, poll=self.poll)

    @staticmethod
    def create(cli, raid_group_id, disks, raid_type=None):
        ret = cli.create_rg(disks, raid_group_id, raid_type)
        ex.raise_if_err(ret, default=ex.VNXCreateRaidGroupError)
        return VNXRaidGroup(raid_group_id, cli)

    def delete(self):
        ret = self._cli.delete_rg(self._get_raid_group_id(), poll=self.poll)
        ex.raise_if_err(ret, default=ex.VNXDeleteRaidGroupError)

    @classmethod
    def get(cls, cli, raid_group_id=None):
        if raid_group_id is None:
            ret = VNXRaidGroupList(cli)
        else:
            ret = VNXRaidGroup(raid_group_id, cli)
        return ret

    @property
    @round_3
    def available_capacity_gbs(self):
        return block_to_gb(self.free_capacity_blocks_non_contiguous)


class VNXRaidGroupList(VNXCliResourceList):
    @classmethod
    def get_resource_class(cls):
        return VNXRaidGroup

    def _get_raw_resource(self):
        return self._cli.get_rg(poll=self.poll)
