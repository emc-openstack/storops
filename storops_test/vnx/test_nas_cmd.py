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

from hamcrest import assert_that, equal_to

from storops.vnx.nas_cmd import NasCommand
from storops.vnx.resource.cifs_share import CifsAccessControl

__author__ = 'Cedric Zhuang'


class NasCommandTest(TestCase):
    def setUp(self):
        self.cmd = NasCommand()

    def test_nas_cel_list(self):
        cmd = ' '.join(self.cmd.nas_cel_list())
        assert_that(cmd, equal_to('/nas/bin/nas_cel -interconnect -l'))

    def test_get_dm_interfaces_all_mover(self):
        cmd = ' '.join(self.cmd.get_dm_interfaces(is_vdm=False))
        assert_that(cmd, equal_to('/nas/bin/nas_server -i -all'))

    def test_get_dm_interfaces_all_vdm(self):
        cmd = ' '.join(self.cmd.get_dm_interfaces(is_vdm=True))
        assert_that(cmd, equal_to('/nas/bin/nas_server -i -vdm -all'))

    def test_get_dm_interfaces_mover_name(self):
        cmd = ' '.join(
            self.cmd.get_dm_interfaces(name='server_2', is_vdm=False))
        assert_that(cmd, equal_to('/nas/bin/nas_server -i server_2'))

    def test_get_dm_interfaces_vdm_name(self):
        cmd = ' '.join(self.cmd.get_dm_interfaces(name='VDM_ESA', is_vdm=True))
        assert_that(cmd, equal_to('/nas/bin/nas_server -i -vdm VDM_ESA'))

    def test_attach_nfs_interface(self):
        cmd = ' '.join(
            self.cmd.attach_nfs_interface('1.1.1.1-0', vdm_name='my'))
        assert_that(cmd,
                    equal_to('/nas/bin/nas_server -vdm my -attach 1.1.1.1-0'))

    def test_detach_nfs_interface(self):
        cmd = ' '.join(
            self.cmd.detach_nfs_interface('1.1.1.1-0', vdm_name='my'))
        assert_that(cmd,
                    equal_to('/nas/bin/nas_server -vdm my -detach 1.1.1.1-0'))

    def test_disable_share_access(self):
        cmd = ' '.join(self.cmd.disable_cifs_share_access('zzz', 'server_2'))
        expected = ('/nas/bin/.server_config server_2 -v sharesd zzz '
                    'set noaccess')
        assert_that(cmd, equal_to(expected))

    def test_allow_share_access(self):
        cmd = ' '.join(self.cmd.allow_cifs_share_access(
            'zzz', 'server_2', 'admin', 'a.dev', CifsAccessControl.READ))
        expected = ('/nas/bin/.server_config server_2 -v sharesd zzz '
                    'grant admin@a.dev=read')
        assert_that(cmd, equal_to(expected))

    def test_deny_share_access(self):
        cmd = ' '.join(self.cmd.deny_cifs_share_access(
            'zzz', 'server_2', 'admin', 'a.dev'))
        expected = ('/nas/bin/.server_config server_2 -v sharesd zzz '
                    'revoke admin@a.dev=fullcontrol')
        assert_that(cmd, equal_to(expected))
