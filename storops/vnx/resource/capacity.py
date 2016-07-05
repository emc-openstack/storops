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

from storops.vnx.resource.disk import VNXDisk
from storops.vnx.resource.block_pool import VNXPool
from storops.vnx.resource.rg import VNXRaidGroup
from storops.lib.common import JsonPrinter, round_3
from storops.lib.converter import mb_to_gb

__author__ = 'Tina Tang'


class VNXCapacity(JsonPrinter):

    _properties = ['used', 'total', 'free_raw_disk', 'free_storage_pool']

    def __init__(self, cli=None):
        super(VNXCapacity, self).__init__()
        self._cli = cli
        self._total = None
        self._free_raw_disk = None
        self._free_storage_pool = None
        self._used = None

    @classmethod
    def get(cls, cli):
        return VNXCapacity(cli)

    @property
    @round_3
    def total(self):
        """Total disk capacity in GB"""
        if self._total is None:
            self._update_disk_capacity()
        return self._total

    @property
    @round_3
    def free_raw_disk(self):
        """Free raw disk capacity in GB

        Physical capacity (in GB) of all unused disks, including disks in empty
        RAID Groups.
        """
        if self._free_raw_disk is None:
            self._update_disk_capacity()
        return self._free_raw_disk

    @property
    @round_3
    def free_storage_pool(self):
        """Free storage pool capacity in GB

        Free storage capacity (in GB) in all storage pools and non-empty RAID
        Groups.
        """
        if self._free_storage_pool is None:
            self._update_free_pool_capacity()
        return self._free_storage_pool

    @property
    @round_3
    def used(self):
        """Total used capacity in GB

        Capacity consumed by LUNs, RAID protection and storage pools for File.
        """
        return self.total - self.free_storage_pool - self.free_raw_disk

    def update(self):
        self._update_free_pool_capacity()
        self._update_disk_capacity()

    def _update_disk_capacity(self):
        disks = VNXDisk.get(self._cli)
        self._total = mb_to_gb(sum([cap for cap in disks.capacity if cap is
                                    not None]))
        self._free_raw_disk = mb_to_gb(
            sum([disk.capacity for disk in disks if disk.state == 'Unbound']))

    def _update_free_pool_capacity(self):
        pools = VNXPool.get(self._cli)
        free_in_pool = sum(pools.available_capacity_gbs)
        rgs = VNXRaidGroup.get(self._cli)
        free_in_rg = sum([rg.available_capacity_gbs for rg in rgs
                          if len(rg.list_of_luns) != 0])
        self._free_storage_pool = free_in_pool + free_in_rg

    def _get_properties(self, dec=0):
        re = {}
        for props in self._properties:
            re[props] = getattr(self, props)
        return re
