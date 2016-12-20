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

from storops.exception import NoIndexException, UnityResourceNotFoundError, \
    UnityNameNotUniqueError, UnityActionNotAllowedError, \
    UnityPerfMonNotEnabledError
from storops.lib.common import clear_instance_cache, instance_cache, \
    get_local_folder
from storops.lib.metric import MetricsDumper
from storops.lib.resource import Resource, ResourceList
from storops.unity import parser
from storops.unity.calculator import calculators
from storops.unity.parser import NestedProperties

__author__ = 'Cedric Zhuang'


class UnityResource(Resource):
    def __init__(self, _id=None, cli=None):
        super(UnityResource, self).__init__()
        self._id = _id
        self._cli = cli
        self._preloaded_properties = None

    @classmethod
    def _get_parser(cls):
        return parser.get_unity_parser(cls.__name__)

    def verify(self):
        if not self.existed:
            raise ValueError(
                'specified {}:{} not exists.'.format(
                    self.__class__.__name__, self.get_id()))
        return self

    def get_id(self):
        ret = None
        if self._id is not None:
            ret = self._id
        elif self._parsed_resource is not None:
            ret = self._parsed_resource.get('id')
            if ret is not None:
                self._id = ret

        if ret is None:
            raise NoIndexException('id is not available for this resource.')
        return ret

    def delete(self, async=False):
        resp = self._cli.delete(self.resource_class, self.get_id(),
                                async=async)
        resp.raise_if_err()
        return resp

    def modify(self, **req_body):
        return self._cli.modify(self.resource_class,
                                self.get_id(), **req_body)

    @property
    def resource_class(self):
        return self._get_parser().name

    @classmethod
    def build_nested_properties_obj(cls):
        return NestedProperties.build(cls.get_nested_properties())

    @classmethod
    def get_nested_properties(cls):
        return None

    def _get_raw_resource(self):
        _id = self.get_id()
        nested_obj = self.build_nested_properties_obj()
        nested_fields = nested_obj.query_fields if nested_obj else None

        res = self._cli.get(self.resource_class, _id,
                            nested_fields=nested_fields)
        # Rest the preloaded the properties to the nested_properties after
        # fetching data from backend
        self.set_preloaded_properties(nested_obj)
        return res

    def _is_updated(self):
        ret = super(UnityResource, self)._is_updated()
        if ret:
            if self.get_preloaded_prop_keys():
                # Return False when only id is parsed besides the
                # preloaded properties
                other = (
                    set(self.parsed_resource.keys()) -
                    set(self.get_preloaded_prop_keys())
                )
                ret = not (
                    len(other) == 1 and
                    len(self.property_names()) -
                    len(self.get_preloaded_prop_keys()) > 1)
            else:
                # Return False when only id is parsed
                ret = not (self.parsed_resource is None or
                           (len(self._parsed_resource) == 1 and
                            len(self.property_names()) > 1))
        return ret

    def _get_properties(self, dec=0):
        if dec < 0 and not self._is_updated():
            props = {'hash': self.__hash__(),
                     'id': self.get_id()}
        else:
            props = super(UnityResource, self)._get_properties(dec)
        return props

    def _parse_raw(self, data):
        return self._get_parser().parse(data, self._preloaded_properties)

    def get_preloaded_prop_keys(self):
        # Returns the preloaded property keys of this object
        # the properties of child object should be skipped

        if not self._preloaded_properties:
            return []
        return self._preloaded_properties.get_properties()

    def _get_property_from_raw(self, item):
        if item in self.metric_names():
            value = self.get_metric_value(item)
        else:
            value = super(UnityResource, self)._get_property_from_raw(item)
            if isinstance(value, UnityResource):
                value.set_cli(self._cli)
        return value

    def property_names(self):
        names = super(UnityResource, self).property_names()
        if self._cli is not None and self._cli.is_perf_metric_enabled(self):
            names.extend(self.metric_names())
        return names

    @property
    def clz_name(self):
        return self._get_parser().resource_class_name

    def metric_names(self):
        return calculators.get_metric_names(self.clz_name)

    def get_metric_value(self, item):
        if not self._cli.is_perf_metric_enabled(self):
            raise UnityPerfMonNotEnabledError()
        return calculators.get_metric_value(
            self.clz_name, item, self._cli, self.get_id())

    def get_metric_timestamp(self):
        curr = self._cli.curr_counter
        if curr is None or len(curr) == 0:
            ret = None
        else:
            ret = curr[0].timestamp
        return ret

    def set_cli(self, cli):
        if cli is not None:
            self._cli = cli

    @classmethod
    def get(cls, cli, _id=None):
        if not isinstance(_id, cls):
            ret = cls(_id=_id, cli=cli)
        else:
            ret = _id
        return ret

    def set_preloaded_properties(self, props):
        self._preloaded_properties = props

    def _get_unity_rsc(self, clz, _id=None, **filters):
        ret = clz.get(cli=self._cli, _id=_id, **filters)
        if 'name' in filters and filters['name'] is not None:
            name = filters['name']
            clz_name = clz.get_resource_class().__name__
            if len(ret) == 0:
                raise UnityResourceNotFoundError(
                    '{}:{} not found.'.format(clz_name, name))
            elif len(ret) > 1:
                raise UnityNameNotUniqueError(
                    'multiple {} with name {} found.'.format(clz_name, name),
                    # throw out the found multiple objects for later analysis
                    objects=ret)
            else:
                ret = ret[0]
        return ret

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            ret = (self.get_id() == other.get_id())
        else:
            ret = False
        return ret

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return super(UnityResource, self).__hash__()

    @property
    def doc(self):
        """ Document string of all retrieved properties.

        Return the string that including the description of this resource
        and the the property description of this resource.
        :return: string
        """
        return self._cli.get_doc(self.__class__)

    def action(self, action, **kwargs):
        return self._cli.action(self.resource_class,
                                self.get_id(),
                                action,
                                **kwargs)

    @property
    def system_version(self):
        if self._cli is None:
            return None
        return self._cli.system_version


class UnitySingletonResource(UnityResource):
    def __init__(self, cli=None):
        super(UnitySingletonResource, self).__init__(self.singleton_id(), cli)

    @classmethod
    def singleton_id(cls):
        return '0'

    @classmethod
    def get(cls, cli, _id=None):
        if not isinstance(_id, cls):
            ret = cls(cli=cli)
        else:
            ret = _id
        return ret

    def delete(self, async=False):
        raise UnityActionNotAllowedError()


class UnityAttributeResource(UnityResource):
    """ work as an attributes collection of another resource

    This kind of resource don't have individual get or update methods.
    They work as a collection of the attributes of another resource.
    """

    def _get_raw_resource(self):
        raise '{} is not a independent resource.'.format(
            self.__class__.__name__)


class UnityResourceList(UnityResource, ResourceList):
    def __init__(self, cli=None, **the_filter):
        UnityResource.__init__(self, cli=cli)
        ResourceList.__init__(self)
        self._rsc_filter = the_filter

    @classmethod
    def get_resource_class(cls):
        raise NotImplementedError(
            'resource class for {} not implemented.'.format(cls.__name__))

    @classmethod
    def _get_parser(cls):
        return parser.get_unity_parser(cls.get_resource_class().__name__)

    @clear_instance_cache
    def update(self, data=None):
        ret = super(UnityResourceList, self).update(data)
        for item in self._list:
            item._cli = self._cli
        return ret

    def _get_raw_resource(self):
        the_filter = {}
        _parser = self._get_parser()
        for k, v in self._rsc_filter.items():
            # if k is like host.id for "host.id eq XXX" rest filter
            keys = k.split('.')
            # ingore the left string after '.' since both are ok
            # 'host=<host_id> or {'host.id': <host_id>}'
            label = _parser.get_property_label(keys[0])
            if not label:
                raise ValueError(
                    '"{}" is not a valid property of {}.'.format(
                        k, self.get_resource_class().__name__))
            # support {'host.id': <host_id>}
            if len(keys) == 2:
                label = k
            the_filter[label] = v
        nested_obj = self.get_resource_class().build_nested_properties_obj()
        nested_fields = nested_obj.query_fields if nested_obj else None
        res = self._cli.get_all(
            self.resource_class, the_filter=the_filter,
            nested_fields=nested_fields)
        self.set_preloaded_properties(nested_obj)
        return res

    def set_cli(self, cli):
        super(UnityResourceList, self).set_cli(cli)
        for item in self:
            if isinstance(item, UnityResource):
                item.set_cli(cli)

    @classmethod
    def get(cls, cli, _id=None, **filters):
        if _id is None:
            ret = cls(cli=cli, **filters)
        else:
            ret = cls.get_resource_class().get(cli=cli, _id=_id)
        return ret

    @classmethod
    def get_list(cls, cli, value):
        if value is None:
            ret = None
        elif isinstance(value, cls):
            ret = value
        elif isinstance(value, (tuple, list, set)):
            ret = [cls.get_resource_class().get(cli, v) for v in value]
        else:
            ret = [cls.get_resource_class().get(cli, value)]
        return ret

    @property
    def first_item(self):
        if len(self) > 0:
            ret = self[0]
        else:
            raise ValueError('no instance available for found.')
        return ret

    def _parse_raw(self, data):
        return self._get_parser().parse_all(data)

    def set_preloaded_properties(self, props):
        for i in self:
            i.set_preloaded_properties(props)

    def _get_resource_instance(self):
        return self.get_resource_class()(cli=self._cli)

    def persist_metric_data(self, filename=None):
        if filename is None:
            filename = self.get_default_metric_csv_filename()
        return self._metrics_dumper.persist_metric_data(filename)

    def get_metrics_csv(self, sep=None):
        return self._metrics_dumper.get_metrics_csv(sep=sep)

    def get_default_metric_csv_filename(self):
        folder = get_local_folder()
        name = '{}_{}.csv'.format(self._cli.ip, self.resource_class_name)
        return os.path.join(folder, name)

    @property
    @instance_cache
    def _metrics_dumper(self):
        def hdr_cb(rsc):
            return [str(rsc.get_metric_timestamp()),
                    rsc.get_id(),
                    rsc._get_name()]

        extra_headers = ['timestamp', 'id', 'name']
        return MetricsDumper(self, extra_headers, hdr_cb)

    @property
    def resource_class_name(self):
        return self._get_resource_instance().resource_class
