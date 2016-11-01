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

import six

from storops.vnx.resource import VNXCliResourceList
from storops.vnx.resource import VNXCliResource
from storops import exception as ex

__author__ = 'Cedric Zhuang'


class VNXSnapList(VNXCliResourceList):
    def __init__(self, cli=None, res=None):
        super(VNXSnapList, self).__init__(cli=cli)
        self._res = res

    @classmethod
    def get_resource_class(cls):
        return VNXSnap

    def _get_raw_resource(self):
        return self._cli.get_snap(res=self._res)


class VNXSnap(VNXCliResource):
    def __init__(self, name=None, cli=None):
        super(VNXSnap, self).__init__()
        self._cli = cli
        self._name = name

    @classmethod
    def create(cls, cli, res, name, allow_rw=None, auto_delete=None,
               keep_for=None):
        out = cli.create_snap(res, name, allow_rw, auto_delete, keep_for)
        msg = 'failed to create snap "{}" for {}'.format(name, res)
        ex.raise_if_err(out, msg, default=ex.VNXCreateSnapError)
        return VNXSnap(name, cli=cli)

    def _get_raw_resource(self):
        return self._cli.get_snap(name=self._name, poll=self.poll)

    @classmethod
    def get(cls, cli, name=None):
        if name is None:
            ret = VNXSnapList(cli)
        else:
            ret = VNXSnap(name, cli)
        return ret

    def delete(self):
        name = self._get_name()
        out = self._cli.delete_snap(name, poll=self.poll)
        ex.raise_if_err(out, default=ex.VNXDeleteSnapError)

    def copy(self, new_name,
             ignore_migration_check=False,
             ignore_dedup_check=False):
        name = self._get_name()
        out = self._cli.copy_snap(name, new_name,
                                  ignore_migration_check,
                                  ignore_dedup_check, poll=self.poll)
        ex.raise_if_err(out, 'failed to copy snap {}.'.format(name),
                        default=ex.VNXSnapError)
        return VNXSnap(name=new_name, cli=self._cli)

    def modify(self, new_name=None, desc=None,
               auto_delete=None, allow_rw=None, keep_for=None):
        name = self._get_name()
        out = self._cli.modify_snap(name, new_name, desc, auto_delete,
                                    allow_rw, keep_for, poll=self.poll)
        ex.raise_if_err(out, 'failed to modify snap {}.'.format(name),
                        default=ex.VNXModifySnapError)
        if new_name is not None:
            self._name = new_name

    @staticmethod
    def get_name(snap):
        if isinstance(snap, VNXSnap):
            if snap._name is not None:
                ret = snap._name
            else:
                ret = snap.name
        elif isinstance(snap, six.string_types):
            ret = snap
        else:
            raise ValueError('invalid snap.')
        return ret
