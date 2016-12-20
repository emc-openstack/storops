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

import os
from datetime import datetime

from storops.exception import VNXPerMonNotEnabledError
from storops.lib.common import instance_cache, clear_instance_cache, \
    get_local_folder
from storops.lib.metric import MetricsDumper
from storops.lib.resource import Resource, ResourceList
from storops.vnx.calculator import calculators
from storops.vnx.parsers import get_vnx_parser

__author__ = 'Cedric Zhuang'


class VNXResource(Resource):
    @classmethod
    def _get_parser(cls):
        return get_vnx_parser(cls.__name__)

    @classmethod
    def resource_class_name(cls):
        return cls._get_parser().resource_class_name

    def _get_value_by_key(self, item):
        ret = super(VNXResource, self)._get_value_by_key(item)
        if ret is None and self._get_parser() is not None:
            prop = self._get_parser().get_property(item)
            if prop and prop.is_resource_list_clazz():
                ret = tuple()
        return ret

    @property
    def system_version(self):
        if self._cli is None:
            return None
        return self._cli.system_version


class _WithPoll(object):
    def __init__(self, r):
        self._resource = r
        self._orig_poll = self._resource.poll

    def __enter__(self):
        pass

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        # return None, do not handle inner exception
        self._resource.poll = self._orig_poll


class VNXCliResource(VNXResource):
    def __init__(self, cli=None):
        super(VNXCliResource, self).__init__()
        self.poll = True
        self._cli = cli
        self.timestamp = None

    def shadow_copy(self):
        ret = super(VNXCliResource, self).shadow_copy()
        ret._cli = self._cli
        ret.poll = self.poll
        ret.timestamp = self.timestamp
        return ret

    def with_poll(self):
        ret = _WithPoll(self)
        self.poll = True
        return ret

    def with_no_poll(self):
        ret = _WithPoll(self)
        self.poll = False
        return ret

    @instance_cache
    def _get_resource_property(self, value):
        value.set_cli(self._cli)
        return value

    def set_cli(self, cli):
        if cli is not None:
            self._cli = cli

    @clear_instance_cache
    def update(self, data=None):
        ret = super(VNXCliResource, self).update(data)
        self.timestamp = datetime.now()
        return ret

    def _get_property_from_raw(self, item):
        if item in self.metric_names():
            value = self.get_metric_value(item)
        else:
            value = super(VNXCliResource, self)._get_property_from_raw(item)
            if isinstance(value, VNXCliResource):
                value = self._get_resource_property(value)
        return value

    def property_names(self):
        names = super(VNXCliResource, self).property_names()
        if self._cli is not None and self._cli.is_perf_metric_enabled(self):
            names.extend(self.metric_names())
        return names

    def metric_names(self):
        return calculators.get_metric_names(self.resource_class_name())

    def get_metric_value(self, item):
        if not self._cli.is_perf_metric_enabled(self):
            raise VNXPerMonNotEnabledError()
        return calculators.get_metric_value(
            self.resource_class_name(), item, self._cli, self)


class WithListPoll(object):
    def __init__(self, rsc_list):
        self._rsc_list = rsc_list
        self._orig_polls = {rsc: rsc.poll for rsc in self._rsc_list}

    def __enter__(self):
        pass

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_val, exc_tb):
        # return None, do not handle inner exception
        for rsc in self._rsc_list:
            rsc.poll = self._orig_polls[rsc]


def _hdr_cb(rsc):
    if hasattr(rsc, 'name'):
        name = rsc.name
    elif hasattr(rsc, 'index'):
        name = rsc.index
    else:
        raise AttributeError('resource should have "name" or "index" defined.')

    return [rsc.timestamp.isoformat(str(' ')), str(name)]


class VNXCliResourceList(VNXCliResource, ResourceList):
    def __init__(self, cli=None):
        VNXCliResource.__init__(self, cli=cli)
        ResourceList.__init__(self)

        extra_headers = ['timestamp', 'name']
        self._metrics_dumper = MetricsDumper(
            self, extra_headers, _hdr_cb)

        self._poll = True

    def shadow_copy(self, *args, **kwargs):
        ret = VNXCliResource.shadow_copy(self)
        ret.set_filter(*args, **kwargs)
        return ret

    @classmethod
    def _get_parser(cls):
        return get_vnx_parser(cls.get_resource_class().__name__)

    @classmethod
    def get_resource_class(cls):
        raise NotImplementedError(
            'should return the class ref of the resource in the list.')

    @classmethod
    def resource_class_name(cls):
        return cls.get_resource_class().resource_class_name()

    @property
    def poll(self):
        return self._poll

    @poll.setter
    def poll(self, value):
        self._poll = value
        if self._is_updated():
            for item in self:
                item.poll = self._poll

    def _get_resource_instance(self):
        clz = self.get_resource_class()
        if issubclass(clz, VNXCliResource):
            ret = clz(cli=self._cli)
            ret.poll = self.poll
        else:
            ret = clz()
        return ret

    @clear_instance_cache
    def update(self, data=None):
        ret = super(VNXCliResourceList, self).update(data)
        for item in self._list:
            item._cli = self._cli
            item.poll = self.poll
        return ret

    def set_cli(self, cli):
        super(VNXCliResourceList, self).set_cli(cli)
        for item in self:
            if isinstance(item, VNXCliResource):
                item.set_cli(cli)

    def persist_metric_data(self, filename=None):
        if filename is None:
            filename = self.get_default_metric_csv_filename()
        return self._metrics_dumper.persist_metric_data(filename)

    def get_default_metric_csv_filename(self):
        folder = get_local_folder()
        name = '{}_{}.csv'.format(self._cli.ip, self.resource_class_name())
        return os.path.join(folder, name)

    def get_metrics_csv(self, sep=None):
        return self._metrics_dumper.get_metrics_csv(sep=sep)
