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
import re

from storops.lib.common import Enum, cache

log = logging.getLogger(__name__)


class VNXEnum(Enum):
    pass


class VNXSPEnum(VNXEnum):
    SP_A = 'SP A'
    SP_B = 'SP B'
    CONTROL_STATION = 'Celerra'

    @classmethod
    def get_int_index(cls):
        return None, cls.SP_A, cls.SP_B, cls.CONTROL_STATION

    @classmethod
    @cache
    def get_to_delete(cls):
        return re.compile('[_. ]')

    @classmethod
    def is_sp(cls, name):
        name = cls.parse(name)
        return name in (cls.SP_A, cls.SP_B)

    @classmethod
    def _normalize(cls, value):
        ret = re.sub(cls.get_to_delete(), '', value)
        if ret is None:
            pass
        elif ret.endswith('a') and not ret.endswith('rra'):
            ret = 'spa'
        elif ret.endswith('b'):
            ret = 'spb'
        elif ret == 'cs':
            ret = 'celerra'
        return ret

    @classmethod
    def from_str(cls, value):
        value = value.lower()
        value = cls._normalize(value)
        ret = None
        for item in cls.get_all():
            if cls._normalize(item.value.lower()) in value:
                ret = item
                break
        else:
            log.info('cannot parse "{}" to a vnx sp.'.format(value))
        return ret

    @classmethod
    def get_sp_index(cls, value):
        value = cls.parse(value)
        if value is None:
            raise ValueError('"{}" is not a valid sp name.'.format(value))
        return value.index

    @property
    def index(self):
        return self.value.lower()[-1]

    @property
    def display_name(self):
        return self.index.upper()


class VNXProvisionEnum(VNXEnum):
    # value of spec "provisioning:type"
    THIN = 'thin'
    THICK = 'thick'
    COMPRESSED = 'compressed'
    DEDUPED = 'deduplicated'

    @classmethod
    def get_option_map(cls):
        return {
            cls.THIN: ['-type', 'Thin'],
            cls.THICK: ['-type', 'NonThin'],
            cls.COMPRESSED: ['-type', 'Thin'],
            cls.DEDUPED: ['-type', 'Thin', '-deduplication', 'on']}


class VNXCompressionRate(VNXEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


class VNXTieringPreference(VNXEnum):
    INVALID = 0
    NONE = 1
    LOWEST_AVAILABLE = 2
    HIGHEST_AVAILABLE = 3


class VNXRelocationPolicy(VNXEnum):
    INVALID = 0
    NONE = 1
    TIER_PREFERENCE = 2
    OPTIMAL = 3


class VNXMigrationRate(VNXEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    ASAP = 'asap'


class VNXTieringEnum(VNXEnum):
    NONE = 'none'
    HIGH_AUTO = 'starthighthenauto'
    AUTO = 'auto'
    HIGH = 'highestavailable'
    LOW = 'lowestavailable'
    NO_MOVE = 'nomovement'

    @classmethod
    def get_option_map(cls):
        return {
            cls.NONE: [],
            cls.HIGH_AUTO: [
                '-initialTier', 'highestAvailable',
                '-tieringPolicy', 'autoTier'],
            cls.AUTO: [
                '-initialTier', 'optimizePool',
                '-tieringPolicy', 'autoTier'],
            cls.HIGH: [
                '-initialTier', 'highestAvailable',
                '-tieringPolicy', 'highestAvailable'],
            cls.LOW: [
                '-initialTier', 'lowestAvailable',
                '-tieringPolicy', 'lowestAvailable'],
            cls.NO_MOVE: [
                '-initialTier', 'optimizePool',
                '-tieringPolicy', 'noMovement']
        }

    @classmethod
    def get_tier(cls, initial, policy):
        ret = None
        for k, v in cls.get_option_map().items():
            if len(v) >= 4:
                v_initial, v_policy = v[1], v[3]
                if (cls.match_option(initial, v_initial) and
                        cls.match_option(policy, v_policy)):
                    ret = k
                    break
                elif cls.match_option(policy, 'noMovement'):
                    """no movement could have different initial tier"""
                    ret = cls.NO_MOVE
                    break
        if ret is None:
            raise ValueError('Initial tier: {}, policy: {} is not valid.'
                             .format(initial, policy))
        return ret

    @staticmethod
    def match_option(output, option):
        return output.replace(' ', '').lower() == option.lower()


class VNXPortType(VNXEnum):
    FC = 'FC'
    ISCSI = 'iSCSI'
    FCOE = 'FCoE'
    SAS = 'SAS'
    ETHERNET = 'ethernet'
    OTHER = 'other'

    @classmethod
    def get_int_index(cls):
        return None, cls.FC, cls.ISCSI, cls.FCOE, cls.SAS

    @classmethod
    def from_str(cls, value):
        if '.' in value:
            value = 'iSCSI'
        elif ':' in value:
            value = 'FC'

        ret = None
        if value is not None:
            for item in cls.get_all():
                if item.is_equal(value):
                    ret = item
                    break
            else:
                cls._raise_invalid_value(value)
        return ret


class VNXSnapType(VNXEnum):
    LUN = 1
    CG = 2


class VNXMirrorViewRecoveryPolicy(VNXEnum):
    MANUAL = 'manual'
    AUTO = 'automatic'

    @classmethod
    def get_option_map(cls):
        return {
            cls.MANUAL: ['-recoverypolicy', 'manual'],
            cls.AUTO: ['-recoverypolicy', 'auto']
        }


class VNXMirrorViewSyncRate(VNXEnum):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class VNXLunType(VNXEnum):
    THIN = 'Thin'
    NON_THIN = 'NonThin'
    SNAP = 'Snap'
    SNAP_MOUNT_POINT = 'Snap'
    COMPRESSED = 'Compressed'
    NON_COMPRESSED = 'NonCompressed'
    DEDUPED = 'Deduped'
    NON_DEDUPED = 'NonDeduped'


class VNXRaidType(VNXEnum):
    RAID0 = 'r0'
    RAID1 = 'r1'
    RAID2 = 'r2'
    RAID3 = 'r3'
    RAID4 = 'r4'
    RAID5 = 'r5'
    RAID6 = 'r6'
    RAID10 = 'r1_0'


class VNXPoolRaidType(VNXEnum):
    RAID0 = 'r_0'
    RAID1 = 'r_1'
    RAID5 = 'r_5'
    RAID6 = 'r_6'
    RAID10 = 'r_10'

    @property
    def min_disk_requirement(self):
        clz = VNXPoolRaidType
        if self is clz.RAID0:
            ret = 2
        elif self is clz.RAID1:
            ret = 2
        elif self is clz.RAID5:
            ret = 3
        elif self is clz.RAID6:
            ret = 4
        elif self is clz.RAID10:
            ret = 4
        else:
            raise ValueError('invalid VNXPoolRaidType supplied.')
        return ret


class VNXAccessLevel(VNXEnum):
    RW = 'rw'
    RO = 'ro'
    ACCESS = 'access'
    ROOT = 'root'


class VNXShareType(VNXEnum):
    NFS = 'nfs'
    CIFS = 'cifs'


class VNXUserScopeEnum(VNXEnum):
    GLOBAL = 'global'
    LOCAL = 'local'


class VNXUserRoleEnum(VNXEnum):
    ADMIN = 'administrator'
    STORAGE_ADMIN = 'storageadmin'
    OPERATOR = 'operator'
    SECURITY_ADMIN = 'securityadministrator'
    DATA_PROTECTION = 'dataprotection'
    LOCAL_DATA_PROTECTION = 'localdataprotection'
    DATA_RECOVERY = 'datarecovery'
    SAN_ADMIN = 'sanadmin'
    NETWORK_ADMIN = 'networkadmin'
    NAS_ADMIN = 'nasadmin'
    VM_ADMIN = 'vmadmin'


class VNXMirrorImageState(VNXEnum):
    SYNCHRONIZED = 'Synchronized'
    OUT_OF_SYNC = 'Out-of-Sync'
    SYNCHRONIZING = 'Synchronizing'
    CONSISTENT = 'Consistent'
    SCRAMBLED = 'Scrambled'
    INCOMPLETE = 'Incomplete'
    LOCAL_ONLY = 'Local Only'
    EMPTY = 'Empty'
