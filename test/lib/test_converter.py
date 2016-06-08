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

from unittest import TestCase

from datetime import datetime
from hamcrest import assert_that, equal_to, none, has_items, instance_of, \
    only_contains

from storops.lib import converter

__author__ = 'Cedric Zhuang'


class ConverterTest(TestCase):
    def test_to_int_arr(self):
        ret = converter.to_int_arr('12, 0, 5, 12')
        assert_that(ret, equal_to([12, 0, 5, 12]))

    def test_to_int_arr_space(self):
        ret = converter.to_int_arr('62 63 306 324')
        assert_that(ret, equal_to([62, 63, 306, 324]))

    def test_to_int_arr_space_str(self):
        ret = converter.to_int_arr('Unbound')
        assert_that(ret, equal_to([]))

    def test_to_wwn(self):
        ret = converter.to_wwn('ab1234')
        assert_that(ret, equal_to('AB:12:34'))

    def test_to_wwn_no_change(self):
        ret = converter.to_wwn('ab:12:34')
        assert_that(ret, equal_to('AB:12:34'))

    def test_to_wwn_not_aligned(self):
        ret = converter.to_wwn('ab123')
        assert_that(ret, equal_to('AB:12:3'))

    def test_to_int_arr_empty_input(self):
        ret = converter.to_int_arr('')
        assert_that(ret, equal_to([]))

    def test_to_int_str_map(self):
        ret = converter.to_int_str_map(
            '62: RAID5 63: RAID5 306: RAID10 324: RAID5')
        assert_that(len(ret), equal_to(4))
        assert_that(ret[62], equal_to('RAID5'))
        assert_that(ret[306], equal_to('RAID10'))

    def test_to_int_str_map_na(self):
        ret = converter.to_int_str_map('N/A')
        assert_that(len(ret), equal_to(0))

    def test_to_int_int_map_unbound(self):
        ret = converter.to_int_int_map('Unbound')
        assert_that(len(ret), equal_to(0))

    def test_to_int_int_map(self):
        ret = converter.to_int_int_map('62: 92 63: 93 306: 94 324: 95')
        assert_that(len(ret), equal_to(4))
        assert_that(ret[62], equal_to(92))
        assert_that(ret[324], equal_to(95))

    def test_str_to_int_invalid_input(self):
        ret = converter.to_int_arr('12, abc, 12c')
        assert_that(ret, only_contains(12))

    def test_arr_to_str(self):
        ret = converter.arr_to_str([5, -12, 7.21])
        assert_that(ret, equal_to('5,-12,7.21'))

    def test_arr_to_str_with_sep(self):
        ret = converter.arr_to_str(['a bc', 112], '|')
        assert_that(ret, equal_to('a bc|112'))

    def test_to_str_arr(self):
        ret = converter.to_str_arr([5, -12, 7.21])
        assert_that(ret, only_contains('5', '-12', '7.21'))

    def test_to_hlu_alu_map(self):
        output = """
                 HLU/ALU Pairs:

                 HLU Number     ALU Number
                 ----------     ----------
                    0               4
                    12              A1
                 """
        alu2hlu = converter.to_alu_hlu_map(output)
        assert_that(alu2hlu[4], equal_to(0))
        assert_that(alu2hlu.get('A1', None), none())

    def test_to_disk_indices(self):
        output = """
        Disks:
        Bus 0 Enclosure 0 Disk 9
        Bus 1 Enclosure 0 Disk 12
        Bus 1 Enclosure 0 Disk 9
        """
        indices = converter.to_disk_indices(output)
        assert_that(indices, has_items('0_0_9', '1_0_12', '1_0_9'))

    def test_number_to_date_int(self):
        ret = converter.vnx_time_to_date(3623881621)
        assert_that(str(ret), equal_to('2015-11-02 01:47:01'))

    def test_number_to_date_float(self):
        ret = converter.vnx_time_to_date(3617925585.15)
        assert_that(str(ret), equal_to('2015-08-25 03:19:45.150000'))

    def test_float_normal(self):
        ret = converter.to_float('1234.5678')
        assert_that(ret, equal_to(1234.5678))

    def test_float_na(self):
        ret = converter.to_float('N/A')
        assert_that(ret, none())

    def test_int_normal(self):
        ret = converter.to_float('1234')
        assert_that(ret, equal_to(1234))

    def test_to_int_arr_from_str_arr(self):
        ret = converter.to_int_arr(['12', '23'])
        assert_that(ret, has_items(12, 23))

    def test_int_disabled(self):
        ret = converter.to_int('Disabled')
        assert_that(ret, none())

    def test_to_float_normal(self):
        ret = converter.to_float('12.34')
        assert_that(ret, equal_to(12.34))

    def test_to_float_percent(self):
        ret = converter.to_float('12.34%')
        assert_that(ret, equal_to(12.34))

    def test_to_float_invalid(self):
        ret = converter.to_float('12.34.56')
        assert_that(ret, none())

    def test_to_hex(self):
        ret = converter.to_hex(13691781134)
        assert_that(ret, equal_to('0x33018000e'))

    def test_to_datetime(self):
        ret = converter.to_datetime('2016-03-02T02:43:34.014Z')
        assert_that(ret, instance_of(datetime))
        assert_that(str(ret), equal_to('2016-03-02 02:43:34.014000+00:00'))

    def test_to_time_delta_more_than_1_day(self):
        ret = converter.to_time_delta("31:02:34.567")
        assert_that(str(ret), equal_to('1 day, 7:02:34.567000'))

    def test_to_time_delta_zero(self):
        ret = converter.to_time_delta("00:00:00.000")
        assert_that(str(ret), equal_to('0:00:00'))

    def test_url_to_host(self):
        url = 'http://www.abc.com:5050/page.xml'
        ret = converter.url_to_host(url)
        assert_that(ret, equal_to('www.abc.com'))

    def test_url_to_host_ssl(self):
        url = 'https://10.0.0.1:4443/page/my.html?filter=name'
        ret = converter.url_to_host(url)
        assert_that(ret, equal_to('10.0.0.1'))

    def test_url_to_host_ipv6(self):
        url = 'https://[2001:db8:a0b:12f0::1%eth0]:21/my.txt'
        ret = converter.url_to_host(url)
        assert_that(ret, equal_to('[2001:db8:a0b:12f0::1%eth0]'))

    def test_url_to_host_default_port(self):
        url = 'https://2001:db8:a0b:12f0::1-eth0/my.txt'
        ret = converter.url_to_host(url)
        assert_that(ret, equal_to('2001:db8:a0b:12f0::1-eth0'))

    def test_url_to_host_default_protocol(self):
        url = '10.0.0.1/my.txt'
        ret = converter.url_to_host(url)
        assert_that(ret, equal_to('10.0.0.1'))

    def test_url_to_host_port(self):
        url = '10.0.0.1:90'
        ret = converter.url_to_host(url)
        assert_that(ret, equal_to('10.0.0.1'))

    def test_url_to_host_suffix(self):
        url = '10.0.0.1/32'
        ret = converter.url_to_host(url)
        assert_that(ret, equal_to('10.0.0.1'))

    def test_url_to_mask_normal(self):
        url = 'https://10.244.211.30/24'
        ret = converter.url_to_mask(url)
        assert_that(ret, equal_to('255.255.255.0'))

    def test_url_to_mask_29_bit(self):
        url = 'https://10.244.211.30/30'
        ret = converter.url_to_mask(url)
        assert_that(ret, equal_to('255.255.255.252'))

    def test_url_to_mask_7_bit(self):
        url = 'https://10.244.211.30/7'
        ret = converter.url_to_mask(url)
        assert_that(ret, equal_to('254.0.0.0'))

    def test_url_to_mask_not_found(self):
        url = 'https://10.244.211.30/router'
        ret = converter.url_to_mask(url)
        assert_that(ret, none())
