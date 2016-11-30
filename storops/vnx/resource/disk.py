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

import re
from collections import Counter

from storops.lib.common import check_text, instance_cache
from storops.vnx.resource import VNXCliResource, VNXCliResourceList

__author__ = 'Cedric Zhuang'


class VNXDisk(VNXCliResource):
    _index_pattern = re.compile('(\w+)_(\w+)_(\w+)')

    def __init__(self, index=None, cli=None):
        super(VNXDisk, self).__init__()
        self._cli = cli
        self._index = index
        if index is not None:
            self.parse_index(self.index)

    @property
    def bus(self):
        return self.parse_index(self._index)[0]

    @property
    def enclosure(self):
        return self.parse_index(self._index)[1]

    @property
    def disk(self):
        return self.parse_index(self._index)[2]

    @property
    def index(self):
        if self._index is None:
            if self.disk_index is not None:
                self._index = '{}_{}_{}'.format(*self.disk_index)
            else:
                raise ValueError('disk index is not initialized.')
        return self._index

    @property
    def index_string(self):
        bus, enc, disk = self.parse_index(self.index)
        return 'bus {} enclosure {} disk {}'.format(bus, enc, disk)

    def _get_raw_resource(self):
        return self._cli.get_disk(poll=self.poll,
                                  *self.parse_index(self._index))

    @classmethod
    def parse_index(cls, index):
        match = re.search(cls._index_pattern, index)
        if match is None:
            raise ValueError('invalid disk index.  disk index must '
                             'be something like '
                             '"1_2_A0", in which "1" is the bus id, "2"'
                             'is the enclosure id and "A0" is the disk id.')
        return match.groups()

    @classmethod
    def get(cls, cli, index=None):
        if index is None:
            ret = VNXDiskList(cli)
        else:
            index = check_text(index).upper()
            ret = VNXDisk(index, cli)
        return ret

    def delete(self):
        return self._cli.delete_disk(self._index, poll=self.poll)

    def install(self):
        return self._cli.install_disk(self._index, poll=self.poll)


class VNXDiskList(VNXCliResourceList):
    def __init__(self, cli=None, disk_indices=None, drive_type=None,
                 capacity=None):
        super(VNXDiskList, self).__init__(cli)
        self._disk_indices = None
        self._drive_type = None
        self._capacity = None

        self._set_filter(disk_indices, drive_type, capacity)

    @staticmethod
    def _normalize_indices(indices):
        return [index.lower() for index in indices if index is not None]

    def _set_filter(self, disk_indices=None, drive_type=None, capacity=None):
        if disk_indices is not None:
            self._disk_indices = self._normalize_indices(disk_indices)
        else:
            self._disk_indices = None
        self._drive_type = drive_type
        self._capacity = capacity

    def set_indices(self, disk_indices):
        self.set_filter(disk_indices=disk_indices)

    def set_drive_type(self, drive_type):
        self.set_filter(drive_type=drive_type)

    def set_capacity(self, capacity):
        self.set_filter(capacity=capacity)

    def _filter(self, disk):
        ret = True
        if self._disk_indices:
            index = disk.index
            ret &= index and index.lower() in self._disk_indices
        if self._drive_type:
            if disk.drive_type is None:
                ret = False
            else:
                ret &= disk.drive_type.lower() == self._drive_type.lower()
        if self._capacity:
            if disk.capacity is None:
                ret = False
            else:
                ret &= disk.capacity == self._capacity
        return ret

    def same_disks(self, count=2):
        """ filter self to the required number of disks with same size and type

        Select the disks with the same type and same size.  If not
        enough disks available, set self to empty.

        :param count: number of disks to retrieve
        :return: disk list
        """
        ret = self
        if len(self) > 0:
            type_counter = Counter(self.drive_type)
            drive_type, counts = type_counter.most_common()[0]
            self.set_drive_type(drive_type)

        if len(self) > 0:
            size_counter = Counter(self.capacity)
            size, counts = size_counter.most_common()[0]
            self.set_capacity(size)

        if len(self) >= count:
            indices = self.index[:count]
            self.set_indices(indices)
        else:
            self.set_indices('N/A')
        return ret

    @classmethod
    def get_resource_class(cls):
        return VNXDisk

    def _get_raw_resource(self):
        return self._cli.get_disk(poll=self.poll)

    @property
    @instance_cache
    def _disk_index_map(self):
        return {disk.index: disk for disk in self}

    def get(self, index):
        if isinstance(index, VNXDisk):
            index = index.index

        return self._disk_index_map.get(index)
