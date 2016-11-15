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
from unittest import TestCase

from hamcrest import equal_to, assert_that, not_none, none, raises

from storops.vnx.enums import VNXSPEnum
from storops.vnx.parsers import VNXCliParser, VNXPropDescriptor, \
    VNXParserConfigFactory
from storops.vnx.resource import get_vnx_parser
from test.vnx.cli_mock import MockCli
from test.vnx.resource.fakes import STORAGE_GROUP_HBA

log = logging.getLogger(__name__)

A = VNXPropDescriptor('-a', 'Prop A (name):', 'prop_a')
B = VNXPropDescriptor('-b', 'Prop B:')
C = VNXPropDescriptor('-c', 'Prop C:')
ID = VNXPropDescriptor(None, 'ID:', is_index=True)


class DemoParser(VNXCliParser):
    def __init__(self):
        super(DemoParser, self).__init__()
        self.add_property(A, B, C, ID)


class DemoParserNonIndex(VNXCliParser):
    def __init__(self):
        super(DemoParserNonIndex, self).__init__()
        self.add_property(VNXPropDescriptor('-b', 'Prop B:'))


class DemoParserRegexIndex(VNXCliParser):
    def __init__(self):
        super(DemoParserRegexIndex, self).__init__()
        self.add_property(
            VNXPropDescriptor(None,
                              r'\s*\w+:(\d+)',
                              'id',
                              is_index=True,
                              is_regex=True,
                              converter=int),
            VNXPropDescriptor(None,
                              r'\s*value:\s*(\w+)',
                              'value',
                              is_regex=True))


class DemoParserMultiIndices(VNXCliParser):
    def __init__(self):
        super(DemoParserMultiIndices, self).__init__()
        self.add_property(
            VNXPropDescriptor(None, 'A:', is_index=True),
            VNXPropDescriptor(None, 'B:', is_index=True),
            VNXPropDescriptor(None, 'C:'),
            VNXPropDescriptor(None, 'D:'))


class VNXCliParserTest(TestCase):
    def test_get_property_options(self):
        options = DemoParser().property_options
        assert_that(' '.join(options), equal_to('-a -b -c'))

    def test_get_index_descriptor(self):
        assert_that(DemoParser().index_property.label, equal_to('ID:'))

    def test_get_index_descriptor_none(self):
        assert_that(DemoParserNonIndex().index_property, none())

    def test_parse(self):
        output = """
                ID: test
                Prop A (Name): ab (c)
                Prop B: d ef
                """
        parser = DemoParser()
        parsed = parser.parse(output, [A, ID, C])

        assert_that(parsed.prop_a, equal_to('ab (c)'))
        assert_that(parsed.prop_c, none())
        assert_that(parsed.id, equal_to('test'))

        def f():
            log.debug(parsed.prop_b)

        assert_that(f, raises(AttributeError))

    def test_parse_empty_prop(self):
        output = """
                ID: test
                Prop A (Name): ab (c)
                Prop B:
                Prop C: abc
                """
        parser = DemoParser()
        parsed = parser.parse(output, [A, ID, B, C])

        assert_that(parsed.id, equal_to('test'))
        assert_that(parsed.prop_a, equal_to('ab (c)'))
        assert_that(parsed.prop_b, equal_to(''))

    def test_parse_regex_label(self):
        output = """
                id:123
                value:abcde
                id:456
                value:ghijk
                """
        parsed = DemoParserRegexIndex().parse_all(output)
        assert_that(len(parsed), equal_to(2))
        for i in parsed:
            if i.id == 123:
                assert_that(i.value, equal_to('abcde'))
            elif i.id == 456:
                assert_that(i.value, equal_to('ghijk'))
            else:
                self.fail('id not recognized.')

    def test_all_options(self):
        options = DemoParser().all_options
        assert_that(options, equal_to(['-a', '-b', '-c']))

    def test_parse_multi_index(self):
        output = """
        A: a0
        B: b0
        C: c0

        A: a0
        B: b0
        D: d0

        A: a0
        B: b1
        C: c1
        """
        parsed = DemoParserMultiIndices().parse_all(output)
        assert_that(len(parsed), equal_to(2))
        a0b0 = next(i for i in parsed if i.b == 'b0')
        assert_that(a0b0, not_none())
        assert_that(a0b0.a, equal_to('a0'))
        assert_that(a0b0.b, equal_to('b0'))
        assert_that(a0b0.c, equal_to('c0'))
        assert_that(a0b0.d, equal_to('d0'))

        a0b1 = next(i for i in parsed if i.b == 'b1')
        assert_that(a0b1, not_none())
        assert_that(a0b1.a, equal_to('a0'))
        assert_that(a0b1.b, equal_to('b1'))
        assert_that(a0b1.c, equal_to('c1'))


class VNXStorageGroupHBAParserTest(TestCase):
    def test_parse(self):
        data = get_vnx_parser("VNXStorageGroupHBA").parse(STORAGE_GROUP_HBA)
        assert_that(data.host_name, equal_to('abc.def.dev'))
        assert_that(data.sp_port, equal_to('A-3v1'))
        assert_that(data.initiator_ip, equal_to('10.244.209.72'))
        assert_that(data.tpgt, equal_to('1'))
        assert_that(data.isid, equal_to('10000000000'))
        assert_that(
            data.hba,
            equal_to(('iqn.1991-05.com.microsoft:abc.def.dev',
                      'SP A', '3')))

    def test_parse_no_header(self):
        output = """
                iqn.1991-05.com.microsoft:abc.def.dev  SP A     1
                Host name:             abc.def.dev
                SPPort:                A-1v0
                Initiator IP:          10.244.209.72
                TPGT:                  1
                ISID:                  10000000000
                """
        data = get_vnx_parser("VNXStorageGroupHBA").parse(output)
        assert_that(data.host_name, equal_to('abc.def.dev'))
        assert_that(data.sp_port, equal_to('A-1v0'))
        assert_that(data.initiator_ip, equal_to('10.244.209.72'))
        assert_that(data.tpgt, equal_to('1'))
        assert_that(data.isid, equal_to('10000000000'))
        assert_that(data.hba,
                    equal_to(('iqn.1991-05.com.microsoft:abc.def.dev',
                              'SP A',
                              '1')))


class VNXStorageGroupParserTest(TestCase):
    def test_parse(self):
        parser = get_vnx_parser('VNXStorageGroup')
        output = MockCli.read_file('storagegroup_-messner_-list_-host_'
                                   '-iscsiAttributes_-gname_microsoft.txt')
        sg = parser.parse(output)
        assert_that(sg.shareable, equal_to(True))
        assert_that(sg.name, equal_to('microsoft'))
        assert_that(
            sg.wwn,
            equal_to('12:34:56:78:9A:BC:DE:F1:23:45:67:89:AB:CD:EF:01'))
        assert_that(sg.alu_hlu_map[4], equal_to(0))
        assert_that(sg.alu_hlu_map[456], equal_to(123))
        assert_that(sg.alu_hlu_map.get(3, None), none())

        # assert for hba members
        assert_that(len(sg.hba_sp_pairs), equal_to(3))
        hba = sg.hba_sp_pairs[0]
        assert_that(hba.host_name, equal_to('abc.def.dev'))


class VNXConsistencyGroupParserTest(TestCase):
    def test_parse(self):
        output = MockCli.read_file('snap_-group_-list_-detail.txt')
        parser = get_vnx_parser('VNXConsistencyGroup')
        cgs = parser.parse_all(output)
        cg = next(c for c in cgs if c.name == 'test cg name')
        assert_that(cg, not_none())
        assert_that(cg.state, equal_to('Ready'))

        cg = next(c for c in cgs if c.name == 'another cg')
        assert_that(cg, not_none())
        assert_that(cg.state, equal_to('Offline'))


class VNXPoolPropertiesTest(TestCase):
    def test_parse(self):
        output = MockCli.read_file('storagepool_-list_-all_-id_1.txt')
        parser = get_vnx_parser('VNXPool')
        pool = parser.parse(output)
        assert_that(pool.state, equal_to('Ready'))
        assert_that(pool.pool_id, equal_to(1))
        assert_that(pool.user_capacity_gbs, equal_to(2329.792))
        assert_that(pool.available_capacity_gbs, equal_to(1473.623))
        assert_that(pool.fast_cache, none())
        assert_that(pool.name, equal_to('Pool_daq'))
        assert_that(pool.total_subscribed_capacity_gbs, equal_to(2701.767))
        assert_that(pool.percent_full_threshold, equal_to(70))


class VNXPoolFeatureParserTest(TestCase):
    # command:  storagepool -feature -info
    output = """
    Is Virtual Provisioning Supported:  true
    Max. Pools:  60
    Max. Disks Per Pool:  1496
    Max. Disks for all Pools:  1496
    Max. Disks Per Operation:  180
    Max. Pool LUNs:  4000
    Min. Pool LUN Size(Blocks):  1
    Max. Pool LUN Size(Blocks):  549755813888
    Max. Pool LUN Size(GBs):  262144.000
    Total Number of Pools:  2
    Total Number of Pool LUNs:  4
    Total Number of all Pool LUNs that are thin:  3
    Total Number of all Pool LUNs that are non-thin:  1
    Number of Disks used in Pools:  5
    Available Disks:
    Bus 0 Enclosure 0 Disk 24
    Bus 0 Enclosure 0 Disk 16
    Bus 0 Enclosure 0 Disk 5
    Bus 0 Enclosure 0 Disk 4
    """

    def test_parse(self):
        parser = get_vnx_parser('VNXPoolFeature')
        parsed = parser.parse(self.output)
        assert_that(parsed.max_pool_luns, equal_to(4000))
        assert_that(parsed.total_pool_luns, equal_to(4))


class VNXLunPropertiesTest(TestCase):
    def test_parse(self):
        output = MockCli.read_file('lun_-list_-all_-l_19.txt')
        parser = get_vnx_parser('VNXLun')
        parsed = parser.parse(output)
        wwn = '60:06:01:60:1A:50:35:00:CC:22:61:D6:76:B1:E4:11'
        assert_that(parsed.wwn, equal_to(wwn))
        assert_that(parsed.name, equal_to('test_lun'))
        assert_that(parsed.lun_id, equal_to(19))
        assert_that(parsed.total_capacity_gb, equal_to(1.0))
        assert_that(parsed.is_thin_lun, equal_to(True))
        assert_that(parsed.is_compressed, equal_to(False))
        assert_that(parsed.deduplication_state, equal_to('Off'))
        assert_that(parsed.tiering_policy, equal_to('No Movement'))
        assert_that(parsed.initial_tier, equal_to('Optimize Pool'))
        assert_that(parsed.state, equal_to('Ready'))
        assert_that(parsed.status, equal_to('OK(0x0)'))
        assert_that(parsed.operation, equal_to('None'))
        assert_that(parsed.current_owner, equal_to(VNXSPEnum.SP_A))
        assert_that(parsed.attached_snapshot, none())


class VNXParserConfigFactoryTest(TestCase):
    def test_read_properties(self):
        name = 'VNXConsistencyGroup'
        prop = get_vnx_parser(name)
        assert_that(prop.resource_class_name, equal_to(name))
        assert_that(prop.data_src, equal_to('cli'))

    def test_properties_sequence_should_align_with_file(self):
        props = get_vnx_parser('VNXSystem')
        assert_that(props.MODEL.sequence, equal_to(0))
        assert_that(props.NAME.sequence, equal_to(5))

    def test_get_rsc_pkg_name(self):
        name = VNXParserConfigFactory.get_rsc_pkg_name()
        assert_that(name, equal_to('storops.vnx.resource'))
