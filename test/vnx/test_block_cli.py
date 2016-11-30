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

from hamcrest import assert_that, contains_string, equal_to, calling, raises, \
    greater_than, has_items

from storops.exception import VNXSystemDownError, VNXCredentialError
from storops.vnx.block_cli import CliClient
from storops.vnx.enums import VNXTieringEnum, VNXProvisionEnum, \
    VNXSPEnum, VNXMigrationRate, VNXLunType, VNXRaidType, VNXUserRoleEnum
from storops.vnx.resource.lun import VNXLun
from test.vnx.cli_mock import patch_cli, extract_command, MockCli, t_cli

__author__ = 'Cedric Zhuang'


class MockCliTest(TestCase):
    def test_get_filename(self):
        params = ('naviseccli -h 1.1.1.1 -user '
                  'a -password a -scope 0 -t 100 -np '
                  'getagent').split()
        assert_that(MockCli.get_filename(params), equal_to('-np_getagent.txt'))

    def test_get_filename_windows(self):
        params = (r'c:\install\naviseccli.exe -h 1.1.1.1 -user '
                  'a -password a -scope 0 -t 100 '
                  'getagent').split()
        assert_that(MockCli.get_filename(params), equal_to('getagent.txt'))


class CliClientTest(TestCase):
    @patch_cli
    def setUp(self):
        self.client = CliClient('10.244.211.30', heartbeat_interval=0)

    @patch_cli
    def test_set_binary(self):
        client = CliClient('1.1.1.1', heartbeat_interval=0,
                           naviseccli='abc')
        assert_that(
            ' '.join(client._heart_beat.get_cmd_prefix('1.1.1.1')),
            equal_to('abc -h 1.1.1.1'))
        client.set_binary('def')
        assert_that(
            ' '.join(client._heart_beat.get_cmd_prefix('1.1.1.1')),
            equal_to('def -h 1.1.1.1'))

    @patch_cli
    def test_password_missing(self):
        def f():
            client = CliClient('1.1.1.1', 'a', heartbeat_interval=0)
            client.get_agent()

        assert_that(f, raises(VNXCredentialError, 'missing'))

    @patch_cli
    def test_set_credential(self):
        client = CliClient('1.1.1.1', 'a', heartbeat_interval=0)
        try:
            client.get_agent()
            self.fail('should have throw exception')
        except VNXCredentialError:
            pass
        client.set_credential(password='a')
        output = client.get_lun(lun_id=0)
        assert_that(output, contains_string('LOGICAL UNIT NUMBER 0'))

    @patch_cli
    def test_get_agent(self):
        out = self.client.get_agent()
        assert_that(out, contains_string('K10'))

    @extract_command
    def test_get_control_with_ip(self):
        cmd = self.client.get_control(ip='1.1.1.1')
        assert_that(cmd, equal_to('[1.1.1.1] getcontrol'))

    @extract_command
    def test_get_control_without_ip(self):
        cmd = self.client.get_control()
        assert_that(cmd, equal_to('getcontrol'))

    @extract_command
    def test_get_agent_with_poll_1(self):
        cmd = self.client.get_agent()
        assert_that(cmd, equal_to('getagent'))

    @extract_command
    def test_get_agent_with_poll_2(self):
        cmd = self.client.get_agent(poll=True)
        assert_that(cmd, equal_to('getagent'))

    @extract_command
    def test_get_agent_no_poll_1(self):
        cmd = self.client.get_agent(poll=False)
        assert_that(cmd, equal_to('-np getagent'))

    @extract_command
    def test_get_pool(self):
        cmd = self.client.get_pool()
        assert_that(cmd, equal_to('storagepool -list -all'))

    @extract_command
    def test_get_pool_two_option(self):
        cmd = self.client.get_pool(name='p0', pool_id=1)
        assert_that(cmd, equal_to('storagepool -list -all -id 1'))

    @extract_command
    def test_get_pool_by_name(self):
        cmd = self.client.get_pool(name="Pool0")
        assert_that(cmd, equal_to('storagepool -list -all -name Pool0'))

    def test_get_pool_by_name_type_error(self):
        def f():
            self.client.get_pool(name=123)

        assert_that(f, raises(ValueError, 'must be text'))

    def test_get_pool_by_id_type_error(self):
        def f():
            self.client.get_pool(pool_id='abc')

        assert_that(f, raises(ValueError, 'must be an int'))

    @extract_command
    def test_get_pool_by_id_number_str(self):
        # no exception raised
        self.client.get_pool(pool_id='1')

    @extract_command
    def test_get_pool_by_id(self):
        cmd = self.client.get_pool(pool_id=1)
        assert_that(cmd, equal_to('storagepool -list -all -id 1'))

    @extract_command
    def test_get_lun(self):
        cmd = self.client.get_lun()
        assert_that(cmd, equal_to('lun -list -all'))

    @extract_command
    def test_get_lun_by_name(self):
        cmd = self.client.get_lun(name="test")
        assert_that(cmd, equal_to('lun -list -all -name test'))

    @extract_command
    def test_get_lun_by_id(self):
        cmd = self.client.get_lun(lun_id=5)
        assert_that(cmd, equal_to('lun -list -all -l 5'))

    @extract_command
    def test_get_snap_lun(self):
        cmd = self.client.get_lun(lun_type=VNXLunType.SNAP)
        assert_that(cmd, equal_to('lun -list -all -showOnly Snap'))

    @extract_command
    def test_get_cg(self):
        cmd = self.client.get_cg()
        assert_that(cmd, equal_to('snap -group -list -detail'))

    @extract_command
    def test_get_cg_by_name(self):
        cmd = self.client.get_cg(name='my_cg')
        assert_that(cmd, equal_to('snap -group -list -id my_cg -detail'))

    @extract_command
    def test_get_sp_port(self):
        cmd = self.client.get_sp_port()
        assert_that(cmd, equal_to('port -list -sp -all'))

    @extract_command
    def test_get_sg(self):
        cmd = self.client.get_sg(engineering=True)
        assert_that(cmd, equal_to('storagegroup -messner -list -host '
                                  '-iscsiAttributes'))

    @extract_command
    def test_get_sg_by_name(self):
        cmd = self.client.get_sg(name='test_sg')
        assert_that(cmd, equal_to('storagegroup -list -host '
                                  '-iscsiAttributes -gname test_sg'))

    @extract_command
    def test_get_pool_feature(self):
        cmd = self.client.get_pool_feature()
        assert_that(cmd,
                    equal_to('storagepool -feature -info '
                             '-isVirtualProvisioningSupported -maxPools '
                             '-maxDiskDrivesPerPool -maxDiskDrivesAllPools '
                             '-maxDiskDrivesPerOp -maxPoolLUNs -minPoolLUNSize'
                             ' -maxPoolLUNSize -numPools -numPoolLUNs '
                             '-numThinLUNs -numDiskDrivesAllPools '
                             '-availableDisks'))

    @extract_command
    def test_get_connection_port(self):
        cmd = self.client.get_connection_port()
        assert_that(cmd, equal_to('connection -getport -all'))

    @extract_command
    def test_get_connection_port_by_sp(self):
        cmd = self.client.get_connection_port(sp='spa')
        assert_that(cmd, equal_to('connection -getport -all -sp a'))

    @extract_command
    def test_get_connection_port_by_port_id(self):
        cmd = self.client.get_connection_port(port_id=8)
        assert_that(cmd, equal_to('connection -getport -all -portid 8'))

    @extract_command
    def test_get_connection_port_by_port_id_and_vport_id(self):
        cmd = self.client.get_connection_port(port_id=6, vport_id=0)
        assert_that(cmd,
                    equal_to('connection -getport -all -portid 6 -vportid 0'))

    @extract_command
    def test_get_connection_port_by_sp_and_port_id_and_vport_id(self):
        cmd = self.client.get_connection_port(sp='a', port_id=6, vport_id=0)
        assert_that(
            cmd,
            equal_to(
                'connection -getport -all -sp a -portid 6 -vportid 0'))

    @extract_command
    def test_ping_node(self):
        cmd = self.client.ping_node('10.244.211.33', sp='a', port_id=10,
                                    count=1)
        assert_that(cmd,
                    equal_to('connection -pingnode -sp a -portid 10 '
                             '-vportid 0 -address 10.244.211.33 -count 1'))

    @extract_command
    def test_create_lun_with_lun_id_pool_id(self):
        cmd = self.client.create_pool_lun(pool_id=0, lun_id=29)
        assert_that(
            cmd,
            equal_to('lun -create -capacity 1 -sq gb -poolId 0 -l 29'))

    @extract_command
    def test_create_lun_with_name(self):
        cmd = self.client.create_pool_lun(pool_name='P0',
                                          lun_name='zzz',
                                          size_gb=10)
        assert_that(
            cmd,
            equal_to('lun -create -capacity 10 -sq gb '
                     '-poolName P0 -name zzz'))

    @extract_command
    def test_create_lun_with_id(self):
        cmd = self.client.create_pool_lun(pool_id=0,
                                          lun_id=29,
                                          size_gb=10)
        assert_that(
            cmd,
            equal_to('lun -create -capacity 10 -sq gb -poolId 0 -l 29'))

    @extract_command
    def test_create_lun_with_tier(self):
        cmd = self.client.create_pool_lun(pool_id=0,
                                          lun_id=29,
                                          tier=VNXTieringEnum.LOW)
        assert_that(
            cmd,
            equal_to('lun -create -capacity 1 -sq gb -poolId 0 -l 29 '
                     '-initialTier lowestAvailable '
                     '-tieringPolicy lowestAvailable'))

    @extract_command
    def test_create_lun_with_provision(self):
        cmd = self.client.create_pool_lun(pool_id=0,
                                          lun_id=129,
                                          provision=VNXProvisionEnum.DEDUPED)
        assert_that(
            cmd,
            equal_to('lun -create -capacity 1 -sq gb -poolId 0 -l 129 '
                     '-type Thin -deduplication on'))

    @extract_command
    def test_create_lun_ignore_threshold(self):
        cmd = self.client.create_pool_lun(pool_id=1,
                                          lun_id=123,
                                          size_gb=12,
                                          ignore_thresholds=True)
        assert_that(
            cmd,
            equal_to('lun -create -capacity 12 -sq gb -poolId 1 '
                     '-l 123 -ignoreThresholds'))

    def test_create_lun_no_pool(self):
        def f():
            self.client.create_pool_lun(lun_id=29)

        assert_that(f, raises(ValueError, 'pool_id or pool_name'))

    def test_create_lun_no_lun(self):
        def f():
            self.client.create_pool_lun(pool_id=0)

        assert_that(f, raises(ValueError, 'lun_id, lun_name'))

    def test_create_lun_invalid_provision(self):
        def f():
            self.client.create_pool_lun(pool_id=0,
                                        lun_id=129,
                                        provision='ABC')

        assert_that(f, raises(ValueError, 'not supported provisioning type'))

    def test_create_lun_invalid_tier(self):
        def f():
            self.client.create_pool_lun(pool_id=0, lun_id=29, tier='NONE')

        assert_that(f, raises(ValueError, 'not supported tiering type'))

    @extract_command
    def test_delete_pool_lun(self):
        cmd = self.client.delete_pool_lun(lun_id=0)
        assert_that(cmd, equal_to('lun -destroy -l 0 -o'))

    @extract_command
    def test_delete_pool_lun_advanced(self):
        cmd = self.client.delete_pool_lun(lun_name='LUN0',
                                          delete_snapshots=True,
                                          force_detach=True)
        assert_that(cmd, equal_to('lun -destroy -name LUN0 '
                                  '-destroySnapshots -forceDetach -o'))

    def test_delete_pool_lun_value_error(self):
        assert_that(calling(self.client.delete_pool_lun),
                    raises(ValueError, 'lun_id, lun_name'))

    @extract_command
    def test_create_sg(self):
        cmd = self.client.create_sg('testsg')
        assert_that(cmd, equal_to('storagegroup -create -gname testsg'))

    @extract_command
    def test_delete_sg(self):
        cmd = self.client.delete_sg('testsg')
        assert_that(cmd, equal_to('storagegroup -destroy -gname testsg -o'))

    @extract_command
    def test_get_snap(self):
        cmd = self.client.get_snap()
        assert_that(cmd, equal_to('snap -list -detail'))

    @extract_command
    def test_get_snap_by_name(self):
        cmd = self.client.get_snap('gan_snap')
        assert_that(cmd, equal_to('snap -list -id gan_snap -detail'))

    @extract_command
    def test_sg_add_hlu(self):
        cmd = self.client.sg_add_hlu('sg0', 11, 22)
        assert_that(cmd, equal_to(
            'storagegroup -addhlu -hlu 11 -alu 22 -gname sg0 -o'))

    @extract_command
    def test_sg_delete_hlu(self):
        cmd = self.client.sg_delete_hlu('sg0', 11)
        assert_that(cmd,
                    equal_to('storagegroup -removehlu -hlu 11 -gname sg0 -o'))

    @extract_command
    def test_set_path(self):
        cmd = self.client.set_path('sg0', 'aaa.bbb.ccc', VNXSPEnum.SP_A, 10,
                                   '10.0.0.1', 'host0')
        assert_that(cmd, equal_to('storagegroup -setpath -gname sg0 '
                                  '-hbauid aaa.bbb.ccc -sp a -spport 10 '
                                  '-ip 10.0.0.1 -host host0 -o'))

    @extract_command
    def test_set_path_with_vport(self):
        cmd = self.client.set_path('sg0', 'aaa.bbb.ccc', VNXSPEnum.SP_A, 10,
                                   '10.0.0.1', 'host0', 1)
        assert_that(cmd, equal_to('storagegroup -setpath -gname sg0 '
                                  '-hbauid aaa.bbb.ccc -sp a -spport 10 '
                                  '-spvport 1 -ip 10.0.0.1 -host host0 -o'))

    @extract_command
    def test_set_path_no_host_ip(self):
        cmd = self.client.set_path('sg0', 'aaa.bbb.ccc', VNXSPEnum.SP_A, 3,
                                   None, 'host0')
        assert_that(cmd, equal_to(
            'storagegroup -setpath -gname sg0 -hbauid aaa.bbb.ccc '
            '-sp a -spport 3 -host host0 -o'))

    def test_set_path_invalid_sp(self):
        def f():
            self.client.set_path('sg0', 'aaa.bbb.ccc', 'abc', 10,
                                 '10.0.0.1', 'host0', 1)

        assert_that(f, raises(ValueError, 'not a valid sp name'))

    @extract_command
    def test_delete_hba(self):
        cmd = self.client.delete_hba('iqn.1998-01.com.vmware:h1')
        assert_that(cmd, equal_to('port -removeHBA -hbauid '
                                  'iqn.1998-01.com.vmware:h1 -o'))

    @extract_command
    def test_create_snap(self):
        cmd = self.client.create_snap(12, 'snap0')
        assert_that(cmd, equal_to('snap -create -res 12 -name snap0 '
                                  '-allowAutoDelete no -allowReadWrite yes'))

    @extract_command
    def test_create_snap_with_keep_for(self):
        cmd = self.client.create_snap(12, 'snap0', keep_for='1h')
        assert_that(cmd, equal_to('snap -create -res 12 -name snap0 '
                                  '-keepFor 1h -allowReadWrite yes'))

    @extract_command
    def test_create_snap_4_cg(self):
        cmd = self.client.create_snap('cg0', 'snap1', False, True)
        assert_that(cmd, equal_to('snap -create -res cg0 -resType CG '
                                  '-name snap1 -allowAutoDelete yes '
                                  '-allowReadWrite no'))

    @extract_command
    def test_delete_snap(self):
        cmd = self.client.delete_snap('snap0')
        assert_that(cmd, equal_to('snap -destroy -id snap0 -o'))

    @extract_command
    def test_migrate_lun(self):
        cmd = self.client.migrate_lun(0, 1, VNXMigrationRate.ASAP)
        assert_that(cmd,
                    equal_to('migrate -start -source 0 -dest 1 -rate asap -o'))

    def test_migrate_lun_error_src(self):
        def f():
            self.client.migrate_lun('a0', 1)

        assert_that(f, raises(ValueError, 'must be an integer'))

    def test_migrate_lun_error_dst(self):
        def f():
            self.client.migrate_lun(0, 'a')

        assert_that(f, raises(ValueError, 'must be an integer'))

    def test_migrate_lun_error_rate(self):
        def f():
            self.client.migrate_lun(0, 1, 'abc')

        assert_that(f, raises(ValueError, 'not a valid value'))

    @extract_command
    def test_get_migration_session_all(self):
        assert_that(self.client.get_migration_session(),
                    equal_to('migrate -list'))

    @extract_command
    def test_get_migration_session(self):
        assert_that(self.client.get_migration_session(11),
                    equal_to('migrate -list -source 11'))

    @extract_command
    def test_cancel_migrate_lun(self):
        assert_that(self.client.cancel_migrate_lun(0),
                    equal_to('migrate -cancel -source 0 -o'))

    def test_cancel_migrate_lun_invalid_src_id(self):
        def f():
            self.client.cancel_migrate_lun(None)

        assert_that(f, raises(ValueError, 'LUN id missing'))

    @extract_command
    def test_create_mount_point_with_id(self):
        cmd = self.client.create_mount_point(primary_lun_id=1,
                                             mount_point_id=2)
        assert_that(cmd,
                    equal_to('lun -create -type snap -primaryLun 1 -l 2'))

    @extract_command
    def test_create_mount_point_with_name(self):
        cmd = self.client.create_mount_point(primary_lun_name='l1',
                                             mount_point_name='m1')
        assert_that(cmd,
                    equal_to('lun -create -type snap '
                             '-primaryLunName l1 -name m1'))

    def test_create_mount_point_missing_primary_lun(self):
        def f():
            self.client.create_mount_point(mount_point_name='m1')

        assert_that(f, raises(ValueError, 'need to be specified'))

    @extract_command
    def test_attach_snap(self):
        cmd = self.client.attach_snap('s1', lun_id=5)
        assert_that(cmd, equal_to('lun -attach -l 5 -snapName s1'))

    @extract_command
    def test_detach_snap(self):
        cmd = self.client.detach_snap(lun_name='l1')
        assert_that(cmd, equal_to('lun -detach -name l1 -o'))

    @extract_command
    def test_modify_lun_name(self):
        cmd = self.client.modify_lun(lun_id=1, new_name='l2')
        assert_that(cmd, equal_to('lun -modify -l 1 -newName l2 -o'))

    @extract_command
    def test_modify_lun_tier(self):
        cmd = self.client.modify_lun(lun_name='l1',
                                     new_tier=VNXTieringEnum.HIGH)
        assert_that(cmd, equal_to('lun -modify -name l1 '
                                  '-initialTier highestAvailable '
                                  '-tieringPolicy highestAvailable -o'))

    @extract_command
    def test_modify_dedup(self):
        cmd = self.client.modify_lun(lun_id=22, dedup=False)
        assert_that(cmd, equal_to('lun -modify -l 22 -deduplication off -o'))

    @extract_command
    def test_expand_pool_lun(self):
        cmd = self.client.expand_pool_lun(12, lun_id=10,
                                          ignore_thresholds=True)
        assert_that(cmd, equal_to(
            'lun -expand -l 10 -capacity 12 -sq gb -ignoreThresholds -o'))

    @extract_command
    def test_create_cg(self):
        cmd = self.client.create_cg('cg1', [0, 2, 4], auto_delete=False)
        assert_that(cmd, equal_to('snap -group -create -name cg1 '
                                  '-allowSnapAutoDelete no -res 0,2,4'))

    @extract_command
    def test_delete_cg(self):
        cmd = self.client.delete_cg('cg1')
        assert_that(cmd, equal_to('snap -group -destroy -id cg1'))

    @extract_command
    def test_add_cg_member(self):
        cmd = self.client.add_cg_member('cg1', 2, 4)
        assert_that(cmd, equal_to('snap -group -addmember -id cg1 -res 2,4'))

    def test_add_cg_member_empty(self):
        out = self.client.add_cg_member('cg1')
        assert_that(out, equal_to(''))

    @extract_command
    def test_delete_cg_member(self):
        cmd = self.client.delete_cg_member('cg1', 2, 4)
        assert_that(cmd, equal_to('snap -group -rmmember -id cg1 -res 2,4'))

    @extract_command
    def test_replace_cg_member(self):
        cmd = self.client.replace_cg_member('cg1', 2, 4)
        assert_that(cmd, equal_to('snap -group -replmember -id cg1 -res 2,4'))

    @extract_command
    def test_copy_snap(self):
        cmd = self.client.copy_snap('s1', 's2', ignore_dedup_check=True)
        assert_that(cmd, equal_to('snap -copy -id s1 -name s2 '
                                  '-ignoreDeduplicationCheck'))

    def test_modify_snap_no_change(self):
        out = self.client.modify_snap('s1', new_name='s1')
        assert_that(out, equal_to(''))

    @extract_command
    def test_modify_snap(self):
        cmd = self.client.modify_snap('s1', 's2', 'snap2', True, False)
        assert_that(cmd, equal_to('snap -modify -id s1 -name s2 -descr snap2 '
                                  '-allowAutoDelete yes -allowReadWrite no'))

    @extract_command
    def test_modify_snap_keep_for(self):
        cmd = self.client.modify_snap('s1', 's2', 'snap2', False, False, '1h')
        assert_that(cmd, equal_to('snap -modify -id s1 -name s2 -descr snap2 '
                                  '-keepFor 1h -allowReadWrite no'))

    @extract_command
    def test_sg_connect_host(self):
        cmd = self.client.sg_connect_host('sg1', 'host1')
        assert_that(cmd, equal_to('storagegroup -connecthost '
                                  '-host host1 -gname sg1 -o'))

    @extract_command
    def test_sg_disconnect_host(self):
        cmd = self.client.sg_disconnect_host('sg1', 'host1')
        assert_that(cmd, equal_to('storagegroup -disconnecthost '
                                  '-host host1 -gname sg1 -o'))

    @extract_command
    def test_get_ndu_all(self):
        cmd = self.client.get_ndu()
        assert_that(cmd, equal_to('ndu -list'))

    @extract_command
    def test_get_ndu(self):
        cmd = self.client.get_ndu('-VNXSnapshots')
        assert_that(cmd, equal_to('ndu -list -name -VNXSnapshots'))

    @extract_command
    def test_enable_compression(self):
        cmd = self.client.enable_compression(12, 'high', 2,
                                             ignore_thresholds=True)
        assert_that(cmd, equal_to('compression -on -l 12 -destPoolId 2 '
                                  '-rate high -ignoreThresholds -o'))

    def test_enable_compression_invalid_rate(self):
        def f():
            self.client.enable_compression(12, 'abc')

        assert_that(f, raises(ValueError, 'not a valid value'))

    @extract_command
    def test_disable_compression(self):
        cmd = self.client.disable_compression(12, True)
        assert_that(cmd,
                    equal_to('compression -off -l 12 -ignoreThresholds -o'))

    @extract_command
    def test_create_mirror_view_default(self):
        cmd = self.client.create_mirror_view('mv1', 23)
        assert_that(cmd,
                    equal_to('mirror -sync -create -name mv1 '
                             '-lun 23 -usewriteintentlog -o'))

    @extract_command
    def test_create_mirror_view_no_write_intent_log(self):
        cmd = self.client.create_mirror_view('mv1', 23, False)
        assert_that(cmd,
                    equal_to('mirror -sync -create -name mv1 '
                             '-lun 23 -nowriteintentlog -o'))

    @extract_command
    def test_delete_mirror_view(self):
        cmd = self.client.delete_mirror_view('mv')
        assert_that(cmd, equal_to('mirror -sync -destroy -name mv -o'))

    @extract_command
    def test_add_mirror_view_image(self):
        cmd = self.client.add_mirror_view_image('mv', '1.1.1.1', '23')
        assert_that(cmd,
                    equal_to('mirror -sync -addimage -name mv '
                             '-arrayhost 1.1.1.1 -lun 23 '
                             '-recoverypolicy auto -syncrate high'))

    @extract_command
    def test_delete_mirror_view_image(self):
        cmd = self.client.delete_mirror_view_image('mv', '10:20:30')
        assert_that(cmd,
                    equal_to('mirror -sync -removeimage -name mv '
                             '-imageuid 10:20:30 -o'))

    @extract_command
    def test_fracture_mirror_view_image(self):
        cmd = self.client.mirror_view_fracture_image('mv', '10:20:30')
        assert_that(cmd,
                    equal_to('mirror -sync -fractureimage -name mv '
                             '-imageuid 10:20:30 -o'))

    @extract_command
    def test_sync_mirror_view_image(self):
        cmd = self.client.mirror_view_sync_image('mv', '10:20:30')
        assert_that(cmd,
                    equal_to('mirror -sync -syncimage -name mv '
                             '-imageuid 10:20:30 -o'))

    @extract_command
    def test_promote_mirror_view_image(self):
        cmd = self.client.mirror_view_promote_image('mv', '10:20:30')
        assert_that(cmd,
                    equal_to('mirror -sync -promoteimage -name mv '
                             '-imageuid 10:20:30 -o'))

    @extract_command
    def test_get_mirror_view(self):
        cmd = self.client.get_mirror_view('mv1')
        assert_that(cmd, equal_to('mirror -sync -list -name mv1'))
        cmd = self.client.get_mirror_view()
        assert_that(cmd, equal_to('mirror -sync -list'))

    @patch_cli(output='network_error.txt')
    def test_ip(self):
        def f():
            cli = CliClient(heartbeat_interval=0)
            cli.set_ip('1.1.1.1', '1.1.1.2')
            cli.execute(['a'])

        assert_that(f, raises(VNXSystemDownError))

    @extract_command
    def test_get_disk_all(self):
        cmd = self.client.get_disk()
        assert_that(cmd, equal_to('getdisk'))

    @extract_command
    def test_get_disk_single(self):
        cmd = self.client.get_disk(4, 0, 'E8')
        assert_that(cmd, equal_to('getdisk 4_0_E8'))

    @extract_command
    def test_delete_disk(self):
        cmd = self.client.delete_disk('0_0_1')
        assert_that(cmd, equal_to('cru_on_off -messner 0_0_1 0'))

    @extract_command
    def test_install_disk(self):
        cmd = self.client.install_disk('0_0_1')
        assert_that(cmd, equal_to('cru_on_off -messner 0_0_1 1'))

    @extract_command
    def test_get_rg_single(self):
        cmd = self.client.get_rg('12')
        assert_that(cmd, equal_to('getrg 12'))

    @extract_command
    def test_get_rg(self):
        cmd = self.client.get_rg()
        assert_that(cmd, equal_to('getrg'))

    @extract_command
    def test_create_rg(self):
        cmd = self.client.create_rg(['1_0_0', '1_0_1', '1_0_3'], 11,
                                    VNXRaidType.RAID5)
        assert_that(cmd, equal_to(
            'createrg 11 1_0_0 1_0_1 1_0_3 -raidtype r5 -o'))

    @extract_command
    def test_delete_rg(self):
        cmd = self.client.delete_rg(11)
        assert_that(cmd, equal_to('removerg 11'))

    @extract_command
    def test_create_pool(self):
        cmd = self.client.create_pool('p1', ['1_0_0', '1_0_1'], 'r_5')
        assert_that(cmd, equal_to('storagepool -create -disks 1_0_0 1_0_1 '
                                  '-rtype r_5 -name p1 -skiprules'))

    @extract_command
    def test_delete_pool(self):
        cmd = self.client.delete_pool(name='p1')
        assert_that(cmd, equal_to('storagepool -destroy -name p1 -o'))

    @extract_command
    def test_rename_storage_pool(self):
        cmd = self.client.modify_storage_pool(pool_id=2, new_name='p1')
        assert_that(cmd, equal_to('storagepool -modify -id 2 -newName p1 -o'))

    @extract_command
    def test_sp_network_status(self):
        cmd = self.client.sp_network_status(VNXSPEnum.SP_A)
        assert_that(cmd, equal_to('networkadmin -get -sp a -all'))

    @extract_command
    def test_list_all_users(self):
        cmd = self.client.list_user()
        assert_that(cmd, equal_to('security -list -type'))

    @extract_command
    def test_list_specified_user(self):
        cmd = self.client.list_user(name='a')
        assert_that(cmd, equal_to('security -list -user a -type'))

    @extract_command
    def test_add_user(self):
        cmd = self.client.add_user('s', 'd', role=VNXUserRoleEnum.OPERATOR)
        assert_that(cmd, equal_to('security -adduser -user s -password d '
                                  '-scope global -role operator -o'))

    @extract_command
    def test_delete_user(self):
        cmd = self.client.delete_user('s')
        assert_that(cmd, equal_to('security -rmuser -user s -scope global -o'))

    @extract_command
    def test_config_iscsi_ip(self):
        cmd = self.client.config_iscsi_ip(
            VNXSPEnum.SP_A, 10, '5.5.5.5', '255.255.255.0', '5.5.5.1')
        assert_that(cmd, equal_to(
            'connection -setport -iscsi -sp a -portid 10 -vportid 0 '
            '-address 5.5.5.5 -subnetmask 255.255.255.0 -gateway 5.5.5.1 -o'))

    @extract_command
    def test_delete_iscsi_ip(self):
        cmd = self.client.delete_iscsi_ip(VNXSPEnum.SP_A, 10)
        assert_that(cmd, equal_to(
            'connection -delport -sp a -portid 10 -vportid 0 -o'))

    @extract_command
    def test_get_array_name(self):
        cmd = self.client.get_array_name()
        assert_that(cmd, equal_to('arrayname'))

    @extract_command
    def test_set_array_name(self):
        cmd = self.client.set_array_name('new_name')
        assert_that(cmd, equal_to('arrayname new_name -o'))

    @patch_cli
    def test_system_version(self):
        assert_that(self.client.system_version, equal_to('05.33.008.3.297'))

    @extract_command
    def test_get_stats_status(self):
        cmd = self.client.set_stats()
        assert_that(cmd, equal_to('setstats'))

    @extract_command
    def test_set_stats_enabled(self):
        cmd = self.client.set_stats(True)
        assert_that(cmd, equal_to('setstats -on'))

    @extract_command
    def test_set_stats_disabled(self):
        cmd = self.client.set_stats(False)
        assert_that(cmd, equal_to('setstats -off'))

    @patch_cli
    def test_get_persist_rsc_list(self):
        persist_rsc_list_2 = t_cli().get_persist_rsc_list()
        assert_that(len(persist_rsc_list_2), greater_than(3))
        assert_that(t_cli().curr_counter.get_rsc_list_collection(),
                    has_items(*persist_rsc_list_2))

    @patch_cli
    def test_get_rsc_perf_csv_data(self):
        lun_list = t_cli().curr_counter.get_rsc_list(VNXLun)
        csv = lun_list.get_metrics_csv()
        assert_that(csv, contains_string('LUN 4'))
        assert_that(csv, contains_string('LUN 5'))
