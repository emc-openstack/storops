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

from contextlib import contextmanager

from storops.vnx.resource import VNXCliResourceList, VNXCliResource
from storops.vnx.resource.lun import VNXLun, VNXLunList
from storops.vnx.enums import VNXCtrlMethod
from storops import exception as ex

__author__ = "Peter Wang"


def convert_lun(luns):
    lun_ids = []
    smp_names = []
    for lun in luns:
        if lun.is_snap_mount_point:
            smp_names.append(lun.name)
        else:
            lun_ids.append(lun.lun_id)
    return lun_ids, smp_names


def normalize_lun(luns, cli):
    if isinstance(luns, int):
        return [VNXLun(lun_id=luns, cli=cli)]
    elif isinstance(luns, VNXLun):
        return [luns]
    elif isinstance(luns, list) or isinstance(luns, VNXLunList):
        return luns
    elif luns is None:
        return []
    else:
        raise ValueError('Invalid format for luns.')


def convert_ioclass(ioclasses):
    names = []
    if ioclasses:
        for ioclass in ioclasses:
            names.append(ioclass.name)
    return names


@contextmanager
def restart_policy(policy):
    VNXIOPolicy.stop_policy(cli=policy._cli)
    try:
        yield policy
    except ex.StoropsException:
        pass
    policy.run_policy()


class VNXIOClassList(VNXCliResourceList):
    def __init__(self, cli=None, name=None):
        super(VNXIOClassList, self).__init__()
        self._cli = cli
        self._name = name

    @classmethod
    def get_resource_class(cls):
        return VNXIOClass

    def _get_raw_resource(self):
        return self._cli.get_ioclass(name=self._name, poll=self.poll)

    def _filter(self, item):
        """Filter the system default class"""
        return 'Background Class' not in item.name


class VNXIOClass(VNXCliResource):
    def __init__(self, name=None, cli=None):
        super(VNXIOClass, self).__init__()
        self._cli = cli
        self._name = name

    def _get_raw_resource(self):
        if self._cli is None:
            raise ValueError('client is not available for this resource.')
        return self._cli.get_ioclass(name=self._name, poll=self.poll)

    @staticmethod
    def get(cli, name=None):
        ret = VNXIOClassList(cli=cli)
        if name:
            ret = VNXIOClass(name=name, cli=cli)
        return ret

    @property
    def luns(self):
        """Aggregator for ioclass_luns and ioclass_snapshots."""
        lun_list, smp_list = [], []
        if self.ioclass_luns:
            lun_list = map(lambda l: VNXLun(lun_id=l.lun_id, name=l.name,
                                            cli=self._cli), self.ioclass_luns)
        if self.ioclass_snapshots:
            smp_list = map(lambda smp: VNXLun(name=smp.name, cli=self._cli),
                           self.ioclass_snapshots)
        return list(lun_list) + list(smp_list)

    @property
    def policy(self):
        """Returns policy which contains this ioclass."""
        policies = VNXIOPolicy.get(cli=self._cli)
        ret = None
        for policy in policies:
            contained = policy.ioclasses.name
            if self._get_name() in contained:
                ret = VNXIOPolicy.get(name=policy.name, cli=self._cli)
                break
        return ret

    @staticmethod
    def create(cli, name, iotype=None, luns=None,
               ctrlmethod=VNXCtrlMethod.NO_CTRL, minsize=None, maxsize=None):
        luns = normalize_lun(luns, cli)
        lun_ids, smp_names = [], []
        if luns:
            lun_ids, smp_names = convert_lun(luns)
        out = cli.create_ioclass(name, iotype, lun_ids, smp_names,
                                 ctrlmethod=ctrlmethod, minsize=minsize,
                                 maxsize=maxsize)
        ex.raise_if_err(out, default=ex.VNXIOClassError)
        return VNXIOClass(name, cli)

    def modify(self, new_name=None, iotype=None, new_luns=None,
               ctrlmethod=None, minsize=None,
               maxsize=None):
        """Overwrite the current properties for a VNX ioclass.

        :param new_name: new name for the ioclass
        :param iotype: can be 'rw', 'r' or 'w'
        :param new_luns: VNXLun list or VNXLunList to replace current LUN
        :param ctrlmethod: the new CtrlMethod
        :param minsize: minimal size in kb
        :param maxsize: maximium size in kb
        """
        if not any([new_name, iotype, new_luns, ctrlmethod]):
            raise ValueError('Cannot apply modification, please specify '
                             'parameters to modify.')
        new_luns = normalize_lun(new_luns, self._cli)
        lun_ids, smp_names = convert_lun(new_luns)

        def _do_modify():
            out = self._cli.modify_ioclass(
                self._get_name(), new_name, iotype, lun_ids, smp_names,
                ctrlmethod, minsize, maxsize)
            ex.raise_if_err(out, default=ex.VNXIOClassError)
        try:
            _do_modify()
        except ex.VNXIOCLassRunningError:
            with restart_policy(self.policy):
                _do_modify()

        return VNXIOClass(new_name if new_name else self._get_name(),
                          self._cli)

    def add_lun(self, luns):
        """A wrapper for modify method.

        .. note:: This API only append luns to existing luns.
        """
        current_luns = self.luns
        current_names = map(lambda x: x.name, self.luns)
        luns = normalize_lun(luns, self._cli)
        to_add = list(filter(lambda x: x.name not in current_names, luns))
        current_luns.extend(to_add)
        self.modify(new_luns=current_luns)

    def remove_lun(self, luns):
        current_luns = self.luns
        luns = normalize_lun(luns, self._cli)
        lun_names = map(lambda x: x.name, luns)
        new_luns = list(filter(lambda x: x.name not in lun_names,
                        current_luns))
        self.modify(new_luns=new_luns)

    def delete(self):
        out = self._cli.delete_ioclass(self._get_name())
        ex.raise_if_err(out, default=ex.VNXIOClassError)
        return VNXIOClass.get(name=self._get_name(), cli=self._cli)

    def add_to_policy(self, policy):
        if not isinstance(policy, VNXIOPolicy):
            policy = VNXIOPolicy(self._cli, policy)
        return policy.add_class(self)


class VNXIOPolicyList(VNXCliResourceList):
    def __init__(self, cli=None, name=None):
        super(VNXIOPolicyList, self).__init__()
        self._cli = cli
        self._name = name

    @classmethod
    def get_resource_class(cls):
        return VNXIOPolicy

    def _get_raw_resource(self):
        return self._cli.get_policy(name=self._name, poll=self.poll)


class VNXIOPolicy(VNXCliResource):
    def __init__(self, name=None, cli=None):
        super(VNXIOPolicy, self).__init__()
        self._name = name
        self._cli = cli

    def _get_raw_resource(self):
        if self._cli is None:
            raise ValueError('client is not available for this resource.')
        return self._cli.get_policy(name=self._name, poll=self.poll)

    @staticmethod
    def get(cli, name=None):
        ret = VNXIOPolicyList(cli=cli)
        if name:
            ret = VNXIOPolicy(cli=cli, name=name)
        return ret

    @staticmethod
    def create(cli, name, ioclasses=None, fail_action=None, time_limit=None,
               eval_window=None):
        ioclass_names = convert_ioclass(ioclasses)
        out = cli.create_policy(name, ioclass_names, fail_action, time_limit,
                                eval_window)
        ex.raise_if_err(out, default=ex.VNXIOPolicyError)
        return VNXIOPolicy(name, cli)

    def modify(self, new_name=None, new_ioclasses=None, time_limit=None,
               fail_action=None, eval_window=None):
        new_names = convert_ioclass(new_ioclasses)

        def _do_modify():
            out = self._cli.modify_policy(
                self._get_name(), new_name, new_names, time_limit,
                fail_action, eval_window)
            ex.raise_if_err(out, default=ex.VNXIOPolicyError)

        try:
            _do_modify()
        except ex.VNXIOPolicyRunningError:
            with restart_policy(self):
                _do_modify()

    def delete(self):
        out = self._cli.delete_policy(self._get_name())
        ex.raise_if_err(out)
        return VNXIOPolicy.get(name=self._get_name(), cli=self._cli)

    def add_class(self, ioclass):
        """Add one VNXIOClass instance to policy.

        .. note: due to the limitation of VNX, need to stop the policy first.
        """
        current_ioclasses = self.ioclasses
        if ioclass.name in current_ioclasses.name:
            return
        current_ioclasses.append(ioclass)
        self.modify(new_ioclasses=current_ioclasses)

    def remove_class(self, ioclass):
        """Remove VNXIOClass instance from policy."""
        current_ioclasses = self.ioclasses
        new_ioclasses = filter(lambda x: x.name != ioclass.name,
                               current_ioclasses)
        self.modify(new_ioclasses=new_ioclasses)

    def run_policy(self):
        out = self._cli.run_policy(self._get_name())
        ex.raise_if_err(out, default=ex.VNXIOPolicyError)

    @staticmethod
    def stop_policy(cli):
        out = cli.stop_policy()
        ex.raise_if_err(out, default=ex.VNXIOPolicyError)

    def measure_policy(self):
        out = self._cli.measure_policy(self._get_name())
        ex.raise_if_err(out, default=ex.VNXIOPolicyError)


class VNXIOClassLunList(VNXCliResourceList):
    @classmethod
    def get_resource_class(cls):
        return VNXIOClassLun

    def _filter(self, item):
        """Filter the wierd outpout.

        :returns: False if contains 'Not Lun Specific'
        """
        return item.existed


class VNXIOClassLun(VNXCliResource):
    pass


class VNXIOClassSnapshot(VNXCliResource):
    pass


class VNXIOClassSnapshotList(VNXCliResourceList):
    @classmethod
    def get_resource_class(cls):
        return VNXIOClassSnapshot
