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

from hamcrest import assert_that, equal_to, has_items, has_item, none

from storops.vnx.enums import VNXSPEnum, VNXProvisionEnum, VNXTieringEnum, \
    VNXRaidType

__author__ = 'Cedric Zhuang'


def verify_lun_0(lun):
    assert_that(lun.lun_id, equal_to(0))
    assert_that(lun.name, equal_to('File_CS0_21132_0_d7'))
    assert_that(lun.state, equal_to('Ready'))
    assert_that(lun.current_owner, equal_to(VNXSPEnum.SP_A))
    assert_that(lun.default_owner, equal_to(VNXSPEnum.SP_A))
    assert_that(lun.wwn, equal_to(
        '60:06:01:60:12:60:3D:00:95:63:38:87:9D:69:E5:11'))
    assert_that(lun.operation, equal_to('None'))
    assert_that(lun.pool_name, equal_to('Pool4File'))
    assert_that(lun.is_thin_lun, equal_to(False))
    assert_that(lun.is_compressed, equal_to(False))
    assert_that(lun.is_dedup, equal_to(False))
    assert_that(lun.is_private, equal_to(False))
    assert_that(lun.tier, equal_to(VNXTieringEnum.HIGH_AUTO))
    assert_that(lun.provision, equal_to(VNXProvisionEnum.THICK))
    assert_that(lun.user_capacity_gbs, equal_to(500.0))
    assert_that(lun.consumed_capacity_gbs, equal_to(512.249))
    assert_that(lun.existed, equal_to(True))
    assert_that(lun.primary_lun, none())
    assert_that(lun.is_snap_mount_point, equal_to(False))


def verify_raid0(rg):
    assert_that(rg.raid_group_id, equal_to(0))
    assert_that(rg.raid_group_type, equal_to(VNXRaidType.RAID5))
    assert_that(rg.state, equal_to('Valid_luns'))
    assert_that(rg.disks.index,
                has_items('0_0_A0', '0_0_A1', '0_0_A2', '0_0_A3', '0_0_A4'))
    assert_that(rg.list_of_luns, has_item(63868))
    assert_that(len(rg.list_of_luns), equal_to(16))
    assert_that(rg.max_number_of_disks, equal_to(16))
    assert_that(rg.max_number_of_luns, equal_to(256))
    assert_that(rg.raw_capacity_blocks, equal_to(4502487040))
    assert_that(rg.logical_capacity_blocks, equal_to(4502478848))
    assert_that(rg.free_capacity_blocks_non_contiguous,
                equal_to(3744083968))
    assert_that(rg.free_contiguous_group_of_unbound_segments,
                equal_to(1749913216))
    assert_that(rg.defrag_expand_priority, equal_to('N/A'))
    assert_that(rg.percent_defragmented, none())
    assert_that(rg.percent_expanded, none())
    assert_that(rg.disk_expanding_onto, equal_to('N/A'))
    assert_that(rg.lun_expansion_enabled, equal_to(False))
    assert_that(rg.legal_raid_types, equal_to(VNXRaidType.RAID5))


def verify_pool_0(pool):
    assert_that(pool.name, equal_to('Pool4File'))
    assert_that(pool.pool_id, equal_to(0))
    assert_that(pool.state, equal_to('Ready'))
    assert_that(pool.status, equal_to('OK(0x0)'))
    assert_that(pool.fast_cache, equal_to(False))
    assert_that(pool.available_capacity_gbs, equal_to(17314.501))
    assert_that(pool.consumed_capacity_gbs, equal_to(540.303))
    assert_that(pool.total_subscribed_capacity_gbs, equal_to(540.053))
    assert_that(pool.user_capacity_gbs, equal_to(17854.805))
    assert_that(pool.current_operation, equal_to('None'))
    assert_that(pool.current_operation_percent_completed, equal_to(0.0))
    assert_that(pool.current_operation_state, equal_to('N/A'))
    assert_that(pool.current_operation_status, equal_to('N/A'))
    assert_that(pool.luns, equal_to([0]))
    assert_that(pool.percent_full_threshold, equal_to(70.0))
    assert_that(pool.existed, equal_to(True))


def verify_disk_4_0_e8(disk):
    assert_that(disk.index_string, equal_to('bus 4 enclosure 0 disk E8'))
    assert_that(disk.bus, equal_to('4'))
    assert_that(disk.enclosure, equal_to('0'))
    assert_that(disk.disk, equal_to('E8'))
    assert_that(disk.vendor_id, equal_to("SEAGATE"))
    assert_that(disk.product_id, equal_to("ST990080 CLAR900"))
    assert_that(disk.product_revision, equal_to("CS18"))
    assert_that(disk.lun,
                has_items(62, 63, 306, 324, 63871, 1200, 326, 355))
    assert_that(disk.type[62], equal_to('RAID5'))
    assert_that(disk.state, equal_to('Enabled'))
    assert_that(disk.hot_spare, equal_to('NO'))
    assert_that(disk.prct_rebuilt[62], equal_to(99))
    assert_that(disk.prct_bound[62], equal_to(92))
    assert_that(disk.serial_number, equal_to('6XS2EAKG'))
    assert_that(disk.sectors, equal_to('90701824 (44288)'))
    assert_that(disk.capacity, equal_to(840313))
    assert_that(disk.private[63], equal_to(335872))
    assert_that(disk.bind_signature, equal_to('0x22c2ed, 0, 56'))
    assert_that(disk.hard_read_errors, equal_to(1))
    assert_that(disk.hard_write_errors, equal_to(2))
    assert_that(disk.soft_read_errors, equal_to(3))
    assert_that(disk.soft_write_errors, equal_to(4))
    assert_that(disk.read_retries, none())
    assert_that(disk.write_retries, none())
    assert_that(disk.remapped_sectors, equal_to('N/A'))
    assert_that(disk.number_of_reads, equal_to(33646149))
    assert_that(disk.number_of_writes, equal_to(5655147))
    assert_that(disk.number_of_luns, equal_to(8))
    assert_that(disk.raid_group_id, equal_to(5))
    assert_that(disk.clariion_part_number, equal_to('DG118032758'))
    assert_that(disk.request_service_time, equal_to('N/A'))
    assert_that(disk.read_requests, equal_to(33646149))
    assert_that(disk.write_requests, equal_to(5655147))
    assert_that(disk.kbytes_read, equal_to(1858798320))
    assert_that(disk.kbytes_written, equal_to(876138634))
    assert_that(disk.stripe_boundary_crossing, none())
    assert_that(disk.drive_type, equal_to('SAS'))
    assert_that(disk.clariion_tla_part_number, equal_to('005049207PWR'))
    assert_that(disk.user_capacity, equal_to(0))
    assert_that(disk.idle_ticks, equal_to(118477646))
    assert_that(disk.busy_ticks, equal_to(1288999))
    assert_that(disk.current_speed, equal_to('6Gbps'))
    assert_that(disk.maximum_speed, equal_to('6Gbps'))
    assert_that(disk.queue_max, none())
    assert_that(disk.queue_avg, none())
    assert_that(disk.prct_idle, equal_to(7))
    assert_that(disk.prct_busy, equal_to(8))
    assert_that(disk.hardware_power_savings_qualified, equal_to(True))
    assert_that(disk.hardware_power_savings_eligible, equal_to(True))
    assert_that(disk.power_savings_state, equal_to('Full Power'))
    assert_that(disk.current_power_savings_log_timestamp, equal_to('N/A'))
    assert_that(disk.spinning_ticks, none())
    assert_that(disk.standby_ticks, none())
    assert_that(disk.number_of_spin_ups, none())
    assert_that(disk.arrivals_with_nonzero_queue, equal_to(8354391))
    assert_that(disk.high_sum_of_seeks, equal_to(1211052417356144))
    assert_that(disk.idle_ticks_spa, equal_to(59428411))
    assert_that(disk.idle_ticks_spb, equal_to(59049235))
    assert_that(disk.busy_ticks_spa, equal_to(456326))
    assert_that(disk.busy_ticks_spb, equal_to(832673))
    assert_that(disk.queue_length, equal_to(72099433))
