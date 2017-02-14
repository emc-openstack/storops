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

import six
from hamcrest import assert_that, raises
from hamcrest import equal_to
from storops import exception

from storops.exception import VNXFsNotFoundError, VNXException, raise_if_err
from storops.vnx.enums import VNXProvisionEnum, \
    VNXTieringEnum, VNXSPEnum, VNXRaidType, \
    VNXMigrationRate, VNXPortType, VNXPoolRaidType
from storops.vnx.nas_client import NasXmlResponse
from storops_test.vnx.nas_mock import MockXmlPost


class VNXErrorTest(TestCase):
    def test_has_error_with_specific_error(self):
        def f():
            msg = ("SP A: Expansion LUN size must be "
                   "greater than current LUN size. (0x712d8e04)")
            raise_if_err(msg)

        assert_that(f, raises(exception.VNXLunExpandSizeError))

    def test_cg_not_found(self):
        def f():
            output = "Cannot find the consistency group."
            raise_if_err(output)

        assert_that(f, raises(exception.VNXConsistencyGroupNotFoundError))

    def test_snap_not_exists(self):
        def f():
            output = "The specified snapshot does not exist."
            raise_if_err(output)

        assert_that(f, raises(exception.VNXSnapNotExistsError))

    def test_pool_lun_not_exists_multi_line(self):
        def f():
            output = """Could not retrieve the specified (pool lun).
                    The (pool lun) may not exist."""
            raise_if_err(output)

        assert_that(f, raises(exception.VNXLunNotFoundError))

    def test_has_error_regular_string_false(self):
        def f():
            output = ("Cannot unbind LUN because "
                      "it's contained in a Storage Group.")
            raise_if_err(output)

        assert_that(f, raises(exception.VNXLunInStorageGroupError))

    def test_has_error_ev_error(self):
        class ForTest(object):
            pass

        error = ForTest()
        error.where = 'EV_ScsiPipe::_sendCommand() - Sense Data'
        error.why = 'SP A: LUN already exists in the specified storage group.'
        error.who = '@(#)libconnect Revision 7.33.6.2.50 on 1/6/2015 21:54:55'

        def f():
            raise_if_err(error)

        assert_that(f, raises(exception.VNXAluAlreadyAttachedError))

    def test_sp_error_not_supported(self):
        def f():
            out = ('Error returned from the target: 10.244.211.32\n'
                   'CLI commands are not supported by the '
                   'target storage system.')
            raise_if_err(out)

        assert_that(f, raises(exception.VNXNotSupportedError))

    def test_sp_error_time_out(self):
        def f():
            out = ("A network error occurred while "
                   "trying to connect: '10.244.211.33'.\n"
                   "Message : select: The connect timed out.")
            raise_if_err(out)

        assert_that(f, raises(exception.VNXSpNotAvailableError))

    def test_raise_if_err_normal(self):
        raise_if_err('')
        # no raises

    def test_raise_if_err_non_empty(self):
        def f():
            raise_if_err('error msg', msg="error received")

        assert_that(f, raises(VNXException, "error received"))

    def test_raise_if_err_lun_not_found(self):
        def f():
            out = ('Could not retrieve the specified (pool lun). '
                   'The (pool lun) may not exist')
            raise_if_err(out)

        assert_that(f, raises(exception.VNXLunNotFoundError))

    def test_raise_if_err_nas_response_input(self):
        def f():
            resp = NasXmlResponse(MockXmlPost.read_file('fs_not_found.xml'))
            resp.raise_if_err()

        assert_that(f, raises(VNXFsNotFoundError, 'not found'))


class VNXProvisionEnumTest(TestCase):
    def test_get_opt_dedup(self):
        opt = VNXProvisionEnum.get_opt(VNXProvisionEnum.DEDUPED)
        assert_that(' '.join(opt), equal_to('-type Thin -deduplication on'))

    def test_get_opt_thin(self):
        opt = VNXProvisionEnum.get_opt(VNXProvisionEnum.THIN)
        assert_that(' '.join(opt), equal_to('-type Thin'))

    def test_get_opt_thick(self):
        opt = VNXProvisionEnum.get_opt(VNXProvisionEnum.THICK)
        assert_that(' '.join(opt), equal_to('-type NonThin'))

    def test_get_opt_compressed(self):
        opt = VNXProvisionEnum.get_opt(VNXProvisionEnum.COMPRESSED)
        assert_that(' '.join(opt), equal_to('-type Thin'))

    def test_get_opt_not_available(self):
        def f():
            VNXProvisionEnum.get_opt('na')

        assert_that(f, raises(ValueError))


class VNXTieringEnumTest(TestCase):
    def test_get_opt(self):
        opt = VNXTieringEnum.get_opt(VNXTieringEnum.HIGH_AUTO)
        assert_that(
            ' '.join(opt),
            equal_to('-initialTier highestAvailable -tieringPolicy autoTier'))

    def test_get_opt_not_available(self):
        def f():
            VNXTieringEnum.get_opt('na')

        assert_that(f, raises(ValueError))

    def test_invalid_tier_enum(self):
        def f():
            VNXTieringEnum('abc')

        assert_that(f, raises(ValueError, 'not a valid VNXTieringEnum'))

    def test_valid_tier_enum(self):
        auto = VNXTieringEnum('auto')
        assert_that(auto, equal_to(VNXTieringEnum.AUTO))


class VNXSPEnumTest(TestCase):
    def test_from_str(self):
        data = {
            'spa': VNXSPEnum.SP_A,
            'sp': None,
            'sp_a': VNXSPEnum.SP_A,
            'SP b': VNXSPEnum.SP_B,
            'a': VNXSPEnum.SP_A,
            'b': VNXSPEnum.SP_B,
            'cs': VNXSPEnum.CONTROL_STATION,
            'Celerra_CS0_21111': VNXSPEnum.CONTROL_STATION,
            'VPI-24092B': VNXSPEnum.SP_B
        }

        for k, v in six.iteritems(data):
            assert_that(VNXSPEnum.parse(k), equal_to(v),
                        'input: {}'.format(k))

    def test_get_sp_index_err(self):
        def f():
            VNXSPEnum.get_sp_index('abc')

        assert_that(f, raises(ValueError, 'not a valid sp'))

    def test_get_sp_index(self):
        assert_that(VNXSPEnum.get_sp_index('spa'), equal_to('a'))

    def test_sp_value(self):
        assert_that(VNXSPEnum.SP_B.value, equal_to('SP B'))

    def test_index(self):
        assert_that(VNXSPEnum.SP_A.index, equal_to('a'))
        assert_that(VNXSPEnum.SP_B.index, equal_to('b'))


class VNXRaidTypeTest(TestCase):
    def test_from_str(self):
        assert_that(VNXRaidType.from_str('r5'), equal_to(VNXRaidType.RAID5))

    def test_disk_requirement(self):
        assert_that(VNXPoolRaidType.RAID5.min_disk_requirement, equal_to(3))


class VNXMigrationRateTest(TestCase):
    def test_text_type(self):
        assert_that(six.text_type(VNXMigrationRate.HIGH),
                    equal_to('{"VNXMigrationRate": {"value": "high"}}'))


class VNXPortTypeTest(TestCase):
    def test_parse_iqn(self):
        ret = VNXPortType.parse('iqn.1992-04.com.emc:c.a.b')
        assert_that(ret, equal_to(VNXPortType.ISCSI))

    def test_parse_wwn(self):
        ret = VNXPortType.parse('50:06:01:60:B6:E0:16:81:'
                                '50:06:01:68:36:E4:16:81')
        assert_that(ret, equal_to(VNXPortType.FC))
