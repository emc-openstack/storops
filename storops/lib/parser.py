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

import glob
import inspect
import logging
import os
import re

import six

import yaml

from storops.lib.common import cache, instance_cache, Enum, \
    get_clz_from_module, EnumList
from storops.lib import converter as cvt
import storops.lib.resource

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class PropMapper(object):
    def __init__(self,
                 label,
                 key=None,
                 option=None,
                 converter=None):
        self.option = option
        self._label = label
        self._key = key
        self.converter = converter

    @property
    def key(self):
        if self._key is None:
            if self.label is None:
                raise ValueError('"label" not found!')
            self._key = self.camel_case_to_under_score(self.label).lower()
        return self._key

    to_delete = re.compile('[\(\)]')
    p0 = re.compile(r"[A-Za-z0-9']+")
    p1 = re.compile(r"([^_])([A-Z]s[a-z]+|[A-Z][a-z]{2})")
    p2 = re.compile(r'([a-z0-9])([A-Z])')

    @classmethod
    def camel_case_to_under_score(cls, value, delimiter='_'):
        value = re.sub(cls.to_delete, '', value)
        value = '_'.join(re.findall(cls.p0, value))
        s1 = re.sub(cls.p1, r'\1_\2', value)
        ret = re.sub(cls.p2, r'\1_\2', s1).lower()
        if delimiter != '_':
            ret = ret.replace('_', delimiter)
        return ret

    @property
    def label(self):
        return self._label.strip()


class PropDescriptor(PropMapper):
    def __init__(self,
                 option,
                 label,
                 key=None,
                 converter=None,
                 is_index=False,
                 end_pattern=None,
                 is_regex=False):
        super(PropDescriptor, self).__init__(label,
                                             key=key,
                                             option=option,
                                             converter=converter)
        self._is_index = is_index
        self._end_pattern = None
        self._is_regex = is_regex
        self.sequence = -1

        # properties setter
        self.end_pattern = end_pattern

        # other initializations
        self._validate_config()

    def _validate_config(self):
        if self.is_regex and self.end_pattern is not None:
            raise ValueError('"is_regex" and "end_pattern" '
                             'are mutual exclusive.')

    @property
    def is_regex(self):
        return self._is_regex

    @property
    def is_index(self):
        return self._is_index

    def convert(self, value):
        c = self.converter
        if c is not None:
            if self.is_parser():
                value = c.parse_all(value)
            elif self.is_resource_clazz():
                value = c().update(value)
            elif self.is_enum() or self.is_enum_list():
                value = c.parse(value)
            elif callable(c):
                value = c(value)
        return value

    def is_resource_list_clazz(self):
        rsc_list_clz = storops.lib.resource.ResourceList
        c = self.converter
        return inspect.isclass(c) and issubclass(c, rsc_list_clz)

    def is_resource_clazz(self):
        rsc_clz = storops.lib.resource.Resource
        c = self.converter
        return inspect.isclass(c) and issubclass(c, rsc_clz)

    def is_enum(self):
        c = self.converter
        return inspect.isclass(c) and issubclass(c, Enum)

    def is_enum_list(self):
        c = self.converter
        return inspect.isclass(c) and issubclass(c, EnumList)

    def is_parser(self):
        c = self.converter
        return isinstance(c, type) and issubclass(c, OutputParser)

    @property
    def end_pattern(self):
        return self._end_pattern

    @end_pattern.setter
    def end_pattern(self, value):
        if isinstance(value, six.string_types) or value is None:
            self._end_pattern = value
        else:
            raise ValueError('value must be a string type.')

    @property
    @instance_cache
    def index_pattern(self):
        if not self.is_regex:
            ret = re.compile(
                "(^\s*{})".format(re.escape(self.label)),
                flags=self.re_flags)
        else:
            ret = re.compile(self.label, flags=self.re_flags)
        return ret

    re_flags = re.MULTILINE | re.IGNORECASE

    @property
    @instance_cache
    def pattern(self):
        if self.end_pattern is None:
            if self.is_regex:
                ret = re.compile(self.label, self.re_flags)
            else:
                ret = re.compile(
                    '^[ \t]*{}[ \t]*(?P<value>.*)[ \t]*$'.format(
                        re.escape(self.label)), self.re_flags)
        else:
            # has 'end_pattern' means we need to match
            # multi-lines including return.
            # do NOT escape 'end_pattern' because it's
            # already a PATTERN.
            self.re_flags |= re.DOTALL
            ret = re.compile(
                '^\s*{}\s*(?P<value>.*){}'.format(
                    re.escape(self.label),
                    self.end_pattern),
                self.re_flags)
        return ret

    def __lt__(self, other):
        if isinstance(other, PropDescriptor):
            ret = self.sequence < other.sequence
        else:
            ret = True
        return ret


class OutputParser(object):
    def __init__(self):
        self._property_map = {}
        self.resource_name = ''

    @property
    def data_src(self):
        raise NotImplementedError('must be implemented by sub-class')

    @property
    def properties(self):
        if self._property_map is None:
            self._property_map = {}
        return self._property_map.values()

    def set_property_map(self, value):
        self._property_map = value

    def add_property(self, *props):
        for prop in props:
            seq = len(self._property_map)
            prop.sequence = seq
            self._property_map[prop.key.upper()] = prop

    def has_property_key(self, key):
        return key.upper() in self._property_map

    def get_property(self, key):
        return self._property_map.get(key.upper(), None)

    def get_property_label(self, key):
        prop = self.get_property(key)
        if prop:
            ret = prop.label
        else:
            ret = None
        return ret

    def get_property_key(self, label):
        for k, v in self._property_map.items():
            if v.label == label:
                ret = k.lower()
                break
        else:
            ret = None
        return ret

    @property
    def property_names(self):
        return sorted(p.key for p in self.properties)

    def parse_all(self, output, properties=None):
        raise NotImplementedError('must be implemented by sub-class')

    def parse(self, output, properties=None):
        raise NotImplementedError('must be implemented by sub-class')

    @property
    def all_options(self):
        return sorted(d.option for d in self.properties
                      if d.option is not None)

    def init_from_config(self, config):
        # do any customized initialization from config in child class
        pass

    @property
    @instance_cache
    def index_property(self):
        indices = self.index_property_list
        # make sure only one index for each parser
        if len(indices) == 1:
            ret = indices[0]
        elif len(indices) > 1:
            # find the first index
            indices.sort(key=lambda i: i.sequence)
            ret = indices[0]
            log.info('multiple index configured.  '
                     'use the first one as the splitter of output.  '
                     'first index is: "{}"'.format(ret.label))
        else:
            ret = None

        return ret

    @property
    def index_property_list(self):
        return sorted(p for p in self.properties
                      if p.is_index is True)

    @property
    def property_options(self):
        return sorted(p.option for p in self.properties
                      if p.option is not None)

    def __getattr__(self, item):
        if item in self._property_map.keys():
            ret = self._property_map[item]
        else:
            ret = super(OutputParser, self).__getattribute__(item)
        return ret


class ParserConfigFactory(object):
    config_filename = 'parser_configs.yaml'

    @classmethod
    def get_parser_clz(cls, data_src):
        raise NotImplementedError('get_base_clz not implemented.')

    @classmethod
    def get_converter(cls, _):
        return None

    @classmethod
    def get_folder(cls):
        return os.path.dirname(inspect.getfile(cls))

    @classmethod
    def get_rsc_pkg_name(cls):
        names = cls.__module__.split('.')[:-1]
        names.append('resource')
        return '.'.join(names)

    def get(self, name):
        config = self.get_config(name)

        parser = self._get_parser_instance(config)
        parser.init_from_config(config)

        self._get_property_map(parser, config)
        parser.resource_class_name = name
        return parser

    def _get_parser_instance(self, config):
        base_clz = self.get_parser_clz(config.data_src)
        parser = base_clz()
        return parser

    def _get_property_map(self, parser, config):
        for v in config.properties:
            p = self.init_descriptor(v)
            parser.add_property(p)

    def get_config(self, name):
        all_configs = self._read_configs()
        if name not in all_configs:
            raise ValueError('cannot find {} in {}.'.format(
                name, self.config_filename))
        return ParserConfig(all_configs[name])

    def _read_configs(self):
        filename = os.path.join(self.get_folder(), self.config_filename)
        with open(filename, 'r') as stream:
            ret = yaml.load(stream)
        return ret

    @instance_cache
    def get_resource_clz_by_name(self, clz_name):
        ret = None
        if isinstance(clz_name, six.string_types):
            sub_module_names = self._rsc_sub_module_names()
            for sub_module_name in sub_module_names:
                ret = get_clz_from_module(sub_module_name, clz_name)
                if ret is not None:
                    break
        return ret

    @instance_cache
    def get_enum_by_name(self, clz_name):
        ret = None
        if isinstance(clz_name, six.string_types):
            enum_module_name = self._get_enum_module_name()
            ret = get_clz_from_module(enum_module_name, clz_name)
        return ret

    def _get_enum_module_name(self):
        names = self.__module__.split('.')[:-1]
        names.append('enums')
        return '.'.join(names)

    @cache
    def _rsc_sub_module_names(self):
        resource_folder = os.path.join(self.get_folder(), 'resource')
        resource_files = glob.glob('{}{}*.py'.format(resource_folder, os.sep))
        ret = []
        for path in resource_files:
            pkg_name = os.path.basename(path).split('.')[0]
            full_pkg_name = '.'.join([self.get_rsc_pkg_name(), pkg_name])
            ret.append(full_pkg_name)
        return ret

    def _get_converter(self, converter_str):
        """find converter function reference by name

        find converter by name, converter name follows this convention:

            Class.method

        or:

            method

        The first type of converter class/function must be available in
        current module.
        The second type of converter must be available in `__builtin__`
        (or `builtins` in python3) module.

        :param converter_str: string representation of the converter func
        :return: function reference
        """
        ret = None
        if converter_str is not None:
            converter_desc_list = converter_str.split('.')
            if len(converter_desc_list) == 1:
                converter = converter_desc_list[0]
                # default to `converter`
                ret = getattr(cvt, converter, None)

                if ret is None:
                    # try module converter
                    ret = self.get_converter(converter)

                if ret is None:
                    ret = self.get_resource_clz_by_name(converter)

                if ret is None:
                    ret = self.get_enum_by_name(converter)

                if ret is None:
                    # try parser config
                    ret = self.get(converter)

            if ret is None and converter_str is not None:
                raise ValueError(
                    'Specified converter not supported: {}'.format(
                        converter_str))
        return ret

    def init_descriptor(self, prop):
        converter = self._get_converter(prop.get('converter', None))
        return PropDescriptor(option=prop.get('option', None),
                              label=prop.get('label', None),
                              key=prop.get('key', None),
                              is_index=prop.get('is_index', None),
                              converter=converter,
                              end_pattern=prop.get('end_pattern', None),
                              is_regex=prop.get('is_regex', None))


class ParserConfig(object):
    def __init__(self, inputs):
        self.data_src = inputs.get('data_src', None)
        self.name = inputs.get('name', None)
        self._properties = inputs.get('properties', None)
        if self._properties is None:
            self._properties = []

    @property
    def properties(self):
        return self._properties

    def add_property(self, prop):
        self._properties.append(prop)
