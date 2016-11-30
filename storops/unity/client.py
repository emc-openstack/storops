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

import six

import storops.unity.resource.type_resource
from storops.connection.connector import UnityRESTConnector
from storops.lib.common import instance_cache, EnumList
from storops.lib.metric import PerfManager
from storops.unity.enums import UnityEnum, UnityEnumList
from storops.unity.resource import UnityResource, UnityResourceList
import storops.unity.resource.system
from storops.unity.resp import RestResponse

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class UnityClient(PerfManager):
    def __init__(self, ip, username, password, port=443, verify=False):
        super(UnityClient, self).__init__()
        self.ip = ip
        self._rest = UnityRESTConnector(ip, port=port, user=username,
                                        password=password,
                                        verify=verify)
        self._system_version = None

    def get_all(self, type_name, base_fields=None, the_filter=None,
                nested_fields=None):
        """Get the resource by resource id.

        :param nested_fields: nested resource fields
        :param base_fields: fields of this resource
        :param the_filter: dictionary of filter like `{'name': 'abc'}`
        :param type_name: Resource type. For example, pool, lun, nasServer.
        :return: List of resource class objects
        """
        fields = self.get_fields(type_name, base_fields, nested_fields)
        the_filter = self.dict_to_filter_string(the_filter)

        url = '/api/types/{}/instances'.format(type_name)

        resp = self.rest_get(url, fields=fields, filter=the_filter)
        ret = resp
        while resp.has_next_page:
            resp = self.rest_get(url, fields=fields, filter=the_filter,
                                 page=resp.next_page)
            ret.entries.extend(resp.entries)
        return ret

    @classmethod
    def dict_to_filter_string(cls, the_filter):
        def _get_non_list_value(k, v):
            if isinstance(v, six.string_types):
                r = '{} eq "{}"'.format(k, v)
            elif isinstance(v, UnityEnum):
                r = '{} eq {}'.format(k, v.value[0])
            elif isinstance(v, UnityResource):
                r = '{} eq "{}"'.format(k, v.get_id())
            else:
                r = '{} eq {}'.format(k, v)
            return r

        if the_filter:
            items = []
            for key in sorted(the_filter.keys()):
                value = the_filter[key]
                if value is None:
                    continue
                if isinstance(value, (list, tuple, UnityEnumList)):
                    list_ret = ' or '.join([_get_non_list_value(key, item)
                                            for item in value])
                    items.append(list_ret)
                else:
                    items.append(_get_non_list_value(key, value))
            if items:
                ret = ' and '.join(items)
            else:
                ret = None
        else:
            ret = None
        return ret

    def rest_get(self, url, fields=None, **params):
        if fields is None:
            fields = []
        params['fields'] = ','.join(map(str, sorted(fields)))
        url = self.assemble_url(url, **params)
        return RestResponse(self._rest.get(url))

    def rest_post(self, url, body=None, **params):
        url = self.assemble_url(url, **params)
        return RestResponse(self._rest.post(url, body=body))

    def rest_delete(self, url, body=None, **params):
        url = self.assemble_url(url, **params)
        return RestResponse(self._rest.delete(url, body=body))

    @classmethod
    def assemble_url(cls, url, **params):
        if not url.startswith('/'):
            url = '/{}'.format(url)
        if 'compact' not in params:
            params['compact'] = True
        param_list = []
        for key in sorted(params.keys()):
            if params[key] is None:
                continue
            param_list.append('{}={}'.format(key, params[key]))
        url = '{}?{}'.format(url, '&'.join(param_list))
        return url

    @instance_cache
    def _get_type_resource(self, type_name):
        type_clz = storops.unity.resource.type_resource.UnityType
        return type_clz(type_name, self)

    def get_fields(self, type_name, base_fields=None, nested_fields=None):
        if base_fields is not None:
            ret = base_fields
        else:
            unity_type = self._get_type_resource(type_name)
            ret = unity_type.fields
        if nested_fields is not None:
            if isinstance(nested_fields, six.text_type):
                nested_fields = tuple([nested_fields])
            ret = ret + nested_fields
        return ret

    def get_doc(self, clz):
        return UnityDoc.get_doc(self, clz)

    def get(self, type_name, obj_id, base_fields=None, nested_fields=None):
        """Get the resource by resource id.

        :param nested_fields: nested resource fields.
        :param type_name: Resource type. For example, pool, lun, nasServer.
        :param obj_id: Resource id
        :param base_fields: Resource fields to return
        :return: List of tuple [(name, res_inst)]
        """
        base_fields = self.get_fields(type_name, base_fields, nested_fields)
        url = '/api/instances/{}/{}'.format(type_name, obj_id)
        return self.rest_get(url, fields=base_fields)

    def post(self, type_name, **kwargs):
        url = '/api/types/{}/instances'.format(type_name)
        body = self.make_body(kwargs)
        return self.rest_post(url, body)

    def action(self, type_name, obj_id, action, **kwargs):
        base_url = '/api/instances/{}/{}/action/{}'
        url = base_url.format(type_name, obj_id, action)
        url_params = {}
        if 'async' in kwargs:
            async = kwargs['async']
            del kwargs['async']
            if async:
                url_params['timeout'] = 0
        body = self.make_body(kwargs, allow_empty=True)
        return self.rest_post(url, body, **url_params)

    def modify(self, type_name, obj_id, **kwargs):
        return self.action(type_name, obj_id, 'modify', **kwargs)

    def type_action(self, type_name, action, **kwargs):
        url = '/api/types/{}/action/{}'.format(type_name, action)
        body = self.make_body(kwargs)
        return self.rest_post(url, body)

    def delete(self, type_name, _id, **kwargs):
        url = '/api/instances/{}/{}'.format(type_name, _id)
        url_params = {'compact': True}
        if 'async' in kwargs:
            async = kwargs['async']
            del kwargs['async']
            if async:
                url_params['timeout'] = 0
        body = self.make_body(kwargs)
        return self.rest_delete(url, body, **url_params)

    @classmethod
    def _is_empty(cls, value):
        if isinstance(value, (dict, tuple, list)) and len(value) == 0:
            ret = True
        else:
            ret = False
        return ret

    @classmethod
    def make_body(cls, value=None, allow_empty=False, **kwargs):
        if value is None and kwargs:
            value = kwargs
        if isinstance(value, dict):
            ret = {}
            for k, v in value.items():
                v = cls.make_body(v, allow_empty=allow_empty)
                if v is not None and (allow_empty or not cls._is_empty(v)):
                    ret[k] = v
        elif isinstance(value, (list, tuple, UnityResourceList,
                                UnityEnumList)):
            ret = [cls.make_body(v, allow_empty=allow_empty) for v in value]
        elif isinstance(value, UnityEnum):
            ret = value.index
        elif isinstance(value, UnityResource):
            ret = {'id': value.get_id()}
        else:
            ret = value
        return ret

    def set_system_version(self, version):
        self._system_version = version

    @property
    def system_version(self):
        if self._system_version is None:
            clz = storops.unity.resource.system.UnityBasicSystemInfo
            self._system_version = clz.get(cli=self).software_version
        return self._system_version


class UnityDoc(object):
    def __init__(self, cli, clz):
        self._cli = cli

        if issubclass(clz, UnityResourceList):
            clz = clz.get_resource_class()
        elif issubclass(clz, EnumList):
            clz = clz.get_enum_class()
        self._clz = clz

    @classmethod
    def get_doc(cls, cli, clz):
        return UnityDoc(cli, clz).doc

    @property
    def doc(self):
        if issubclass(self._clz, UnityResource):
            ret = self._get_unity_resource_doc()
        elif issubclass(self._clz, UnityEnum):
            ret = self._get_unity_enum_doc()
        else:
            raise ValueError(
                'get_doc not support {}.'.format(self._clz.__name__))
        return ret

    def _get_unity_enum_doc(self):
        docs = self._header
        docs.append('Members:')
        docs.append('--------')
        props = []
        for index in sorted(self._clz.indices()):
            doc = self._get_doc(value=index)
            props.append((index, doc))
        docs += self.format_prop(props,
                                 header=('Enum Index:', 'Description:'))
        return '\n'.join(docs)

    def _get_unity_resource_doc(self):
        docs = self._header
        docs.append('Properties:')
        docs.append('-----------')
        props = []
        for name in self._clz().property_names():
            field = self._clz.get_property_label(name)
            if field:
                doc = self._get_doc(field=field)
                props.append((name, doc))
        docs += self.format_prop(props,
                                 header=('Property Name:', 'Description:'))
        return '\n'.join(docs)

    @property
    def _header(self):
        title = self._clz.__name__
        ret = [title, '=' * len(title)]
        desc = self._get_doc()
        if desc:
            ret.append(desc)
        ret.append('')
        return ret

    @property
    @instance_cache
    def rsc_name(self):
        if issubclass(self._clz, UnityResource):
            ret = self._clz().resource_class
        elif issubclass(self._clz, UnityEnum):
            ret = self._clz.__name__
        else:
            ret = self._clz
        return ret

    @classmethod
    def format_prop(cls, props, header=None):
        if header is not None:
            props.insert(0, header)

        ret = []
        if props:
            max_char_counts = cls.get_column_max_len(props)
            fmt_str = cls.get_fmt_str(max_char_counts)
            for prop in props:
                ret.append(fmt_str.format(*map(str, prop)).strip())
        return ret

    @staticmethod
    def get_column_max_len(array):
        max_char_count = []
        if array:
            column_size = len(array[0])
            for i in range(column_size):
                max_len = 0
                for prop in array:
                    max_len = max(max_len, len(str(prop[i])))
                max_char_count.append(max_len)
        return max_char_count

    @staticmethod
    def get_fmt_str(max_char_counts, padding=2):
        out = []
        for count in max_char_counts:
            out.append('{{:{}}}'.format(count + padding))
        return ''.join(out)

    def _get_doc(self, field=None, value=None):
        # noinspection PyProtectedMember
        unity_type = self._cli._get_type_resource(self.rsc_name)
        ret = None
        if field is not None:
            if unity_type.attributes:
                for attr in unity_type.attributes:
                    if field == attr.get('name'):
                        ret = attr.get('description')
                        break
        elif value is not None:
            if unity_type.attributes:
                for attr in unity_type.attributes:
                    if value == attr.get('initialValue'):
                        ret = attr.get('description')
                        break
        else:
            ret = unity_type.description

        if ret:
            ret = ret.strip()
        return ret
