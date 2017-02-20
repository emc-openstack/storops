# coding=utf-8
# Copyright (c) 2017 Dell Inc. or its subsidiaries.
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

from hamcrest import assert_that, equal_to, instance_of, raises

from storops_test.vnx.cli_mock import t_cli, patch_cli

from storops.vnx.resource.nqm import VNXIOClass, VNXIOClassList, VNXIOPolicy, \
    VNXLun, normalize_lun

__author__ = "Peter Wang"


class VNXIOClassTest(TestCase):
    def test_normalize_lun(self):
        def _inner():
            normalize_lun('invalid', t_cli())
        assert_that(_inner, raises(ValueError, 'Invalid format'))

    @patch_cli
    def test_ioclass_all(self):
        ioclass_list = VNXIOClassList(cli=t_cli())
        assert_that(len(ioclass_list), equal_to(6))
        assert_that(ioclass_list[0], instance_of(VNXIOClass))

    @patch_cli
    def test_ioclass(self):
        ioclass = VNXIOClass(name='with_luns_snaps', cli=t_cli())
        assert_that(ioclass.name, equal_to('with_luns_snaps'))
        assert_that(ioclass.state, equal_to('Idle'))
        assert_that(ioclass.io_type, equal_to('ReadWrite'))
        assert_that(ioclass.io_size_range, equal_to('Any'))
        assert_that(ioclass.control_method, equal_to('Limit'))
        assert_that(ioclass.metric_type, equal_to('Bandwidth'))
        assert_that(ioclass.goal_value, equal_to('1000.0 MB/s'))
        map(lambda l: assert_that(l, instance_of(VNXLun)),
            ioclass.luns)
        assert_that(len(ioclass.luns), equal_to(2))
        assert_that(ioclass.policy, instance_of(VNXIOPolicy))
        assert_that(ioclass.policy.name, equal_to('new_name_test'))

    @patch_cli
    def test_class_multiple_luns(self):
        ioclass = VNXIOClass(name='with_3_luns', cli=t_cli())
        assert_that(ioclass.state, equal_to('Idle'))
        assert_that(ioclass.io_type, equal_to('ReadWrite'))
        assert_that(ioclass.io_size_range, equal_to('Any'))
        assert_that(ioclass.control_method, equal_to('No Control'))
        map(lambda l: assert_that(l, instance_of(VNXLun)),
            ioclass.luns)
        assert_that(len(ioclass.luns), equal_to(3))

    @patch_cli
    def test_ioclass_nolun(self):
        ioclass = VNXIOClass(name='simple', cli=t_cli())
        assert_that(ioclass.name, equal_to('simple'))
        assert_that(ioclass.state, equal_to('Idle'))
        assert_that(ioclass.status, equal_to('Ready'))
        assert_that(len(ioclass.luns), equal_to(0))

    @patch_cli
    def test_create_ioclass(self):
        ioclass = VNXIOClass.create(cli=t_cli(), name="simple",
                                    iotype='rw')
        assert_that(ioclass.name, equal_to('simple'))

    @patch_cli
    def test_create_ioclass_with_lun(self):
        lun2 = VNXLun(name='lun2', cli=t_cli())
        ioclass = VNXIOClass.create(cli=t_cli(), name="simple",
                                    iotype='rw', luns=lun2)
        assert_that(ioclass.name, equal_to('simple'))

    @patch_cli
    def test_delete_ioclasse(self):
        ioclass = VNXIOClass(name='to_delete', cli=t_cli())
        deleted = ioclass.delete()
        assert_that(deleted.existed, equal_to(False))

    @patch_cli
    def test_add_lun_to_ioclass(self):
        ioclass = VNXIOClass(name='with_luns_snaps', cli=t_cli())
        lun1 = VNXLun(lun_id=1, cli=t_cli())
        ioclass.add_lun(lun1)
        # Add via lun id
        ioclass.add_lun(2)

    @patch_cli
    def test_add_lun_to_running_ioclass(self):
        ioclass = VNXIOClass(name='running_ioclass', cli=t_cli())
        lun1 = VNXLun(lun_id=1, cli=t_cli())

        ioclass.add_lun(lun1)

    @patch_cli
    def test_remove_lun(self):
        ioclass = VNXIOClass(name='with_luns_snaps', cli=t_cli())
        ioclass.remove_lun(1)
        lun1 = VNXLun(lun_id=2, cli=t_cli())
        ioclass.remove_lun(lun1)

    @patch_cli
    def test_add_to_policy(self):
        ioclass = VNXIOClass(name='simple', cli=t_cli())
        policy = VNXIOPolicy(name='with_ioclass', cli=t_cli())
        ioclass.add_to_policy(policy)


class VNXIOPolicyTest(TestCase):
    @staticmethod
    def get_policy():
        return VNXIOPolicy(name='simple')

    @patch_cli
    def test_policy(self):
        policy = VNXIOPolicy(name='with_ioclass', cli=t_cli())
        assert_that(policy.name, equal_to('with_ioclass'))
        assert_that(policy.status, equal_to('Ready'))
        assert_that(policy.state, equal_to('Idle'))

    @patch_cli
    def test_create_policy(self):
        policy = VNXIOPolicy.create(name='new_policy', cli=t_cli())
        assert_that(policy.status, equal_to('Warning'))

    @patch_cli
    def test_delete_policy(self):
        policy = VNXIOPolicy(name='to_delete', cli=t_cli())
        deleted = policy.delete()
        assert_that(deleted.existed, equal_to(False))

    @patch_cli
    def test_stop_policy(self):
        VNXIOPolicy.stop_policy(cli=t_cli())

    @patch_cli
    def test_run_policy(self):
        policy = VNXIOPolicy(name='simple', cli=t_cli())
        policy.run_policy()

    @patch_cli
    def test_measure_policy(self):
        policy = VNXIOPolicy(name='simple', cli=t_cli())
        policy.measure_policy()

    @patch_cli
    def test_add_class_to_policy(self):
        policy = VNXIOPolicy(name='with_ioclass', cli=t_cli())
        ioclass = VNXIOClass(name='with_luns_snaps', cli=t_cli())
        policy.add_class(ioclass)

    @patch_cli
    def test_add_class_to_running_policy(self):
        policy = VNXIOPolicy(name='running_policy', cli=t_cli())
        ioclass = VNXIOClass(name='with_luns_snaps', cli=t_cli())

        policy.add_class(ioclass)

    @patch_cli
    def test_remove_class_already_removed(self):
        policy = VNXIOPolicy(name='with_ioclass', cli=t_cli())
        ioclass = VNXIOClass(name='with_luns_snaps', cli=t_cli())
        policy.remove_class(ioclass)

    @patch_cli
    def test_remove_class_from_existing(self):
        policy = VNXIOPolicy(name='with_ioclass', cli=t_cli())
        ioclass = VNXIOClass(name='simple', cli=t_cli())
        policy.remove_class(ioclass)
