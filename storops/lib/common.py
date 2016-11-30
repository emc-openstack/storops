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

import errno
import functools
import inspect
import json
import logging
import sys
import threading
from functools import partial
from os import path, makedirs, stat

import cachez
import math
import six
from enum import Enum as _Enum
from retryz import retry

import storops.exception

log = logging.getLogger(__name__)


class JsonPrinter(object):
    def _get_properties(self, dec=0):
        raise NotImplementedError('need a property-value dictionary')

    def get_dict_repr(self, dec=0):
        props = self._get_properties(dec)
        props = dict((k, v) for k, v in props.items() if v is not None)
        return {self.__class__.__name__: props}

    def json(self, indent=None):
        return json.dumps(self.get_dict_repr(), indent=indent, sort_keys=True)

    def __repr__(self):
        return self.json(indent=4)

    def __str__(self):
        return self.json()


class EnumList(JsonPrinter):
    def _get_properties(self, dec=0):
        super(EnumList, self)._get_properties(dec)

    def __init__(self):
        super(EnumList, self).__init__()
        self._list = []
        self._iter = None

    @classmethod
    def get_enum_class(cls):
        raise NotImplementedError('enum class of this list is not defined.')

    @classmethod
    def parse(cls, values):
        ret = None
        if values is not None:
            ret = cls()
            ret._list = [ret.get_enum_class().parse(v) for v in values]
        return ret

    def get_dict_repr(self, dec=0):
        items = [item.get_dict_repr(dec - 1) for item in self.list]
        return {self.__class__.__name__: items}

    @property
    def list(self):
        return self._list

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        self._iter = self.list.__iter__()
        return self

    def next(self):
        return next(self._iter)

    def __next__(self):
        return self.next()

    def __getitem__(self, item):
        return self.list[item]


class Enum(JsonPrinter, _Enum):
    @classmethod
    def verify(cls, value, allow_none=True):
        if value is None and not allow_none:
            raise ValueError(
                'None is not allowed here for {}.'.format(cls.__name__))
        elif value is not None and not isinstance(value, cls):
            raise ValueError('{} is not an instance of {}.'
                             .format(value, cls.__name__))

    @classmethod
    def get_all(cls):
        return list(cls)

    @classmethod
    def get_opt(cls, value):
        option_map = cls.get_option_map()
        if option_map is None:
            raise NotImplementedError('Option map is not defined for {}.'
                                      .format(cls.__name__))

        ret = option_map.get(value, None)
        if ret is None:
            raise ValueError("{} is not a valid option for {}."
                             .format(value, cls.__name__))
        return ret

    @classmethod
    def parse(cls, value):
        if isinstance(value, six.string_types):
            ret = cls.from_str(value)
        elif isinstance(value, six.integer_types):
            ret = cls.from_int(value)
        elif isinstance(value, cls):
            ret = value
        elif value is None:
            ret = None
        else:
            raise ValueError(
                'not supported value type: {}.'.format(type(value)))
        return ret

    def _get_properties(self, dec=0):
        return {'value': self.value}

    def is_equal(self, value):
        if isinstance(self.value, six.string_types):
            ret = self.value.lower() == value.lower()
        elif isinstance(self.value, six.integer_types):
            ret = self.value == int(value)
        else:
            ret = self.value == value
        return ret

    @classmethod
    def from_int(cls, value):
        ret = None
        int_index = cls.get_int_index()
        if int_index is not None:
            try:
                ret = int_index[value]
            except IndexError:
                pass
        else:
            try:
                ret = next(i for i in cls.get_all() if i.is_equal(value))
            except StopIteration:
                pass
        if ret is None:
            cls._raise_invalid_value(value)
        return ret

    @classmethod
    def from_str(cls, value):
        ret = None
        if value is not None:
            for item in cls.get_all():
                if item.is_equal(value):
                    ret = item
                    break
            else:
                cls._raise_invalid_value(value)
        return ret

    @classmethod
    def _raise_invalid_value(cls, value):
        msg = '{} is not a valid value for {}.'.format(value, cls.__name__)
        log.warn(msg)
        raise storops.exception.EnumValueNotFoundError(msg)

    @classmethod
    def get_option_map(cls):
        raise NotImplementedError('should be implemented by child class.')

    @classmethod
    def get_int_index(cls):
        return None

    @classmethod
    def values(cls):
        return [m.value for m in cls.__members__.values()]

    @classmethod
    def enum_name(cls):
        return cls.__name__

    def __str__(self):
        return JsonPrinter.__str__(self)

    def __repr__(self):
        return JsonPrinter.__repr__(self)

    def get_dict_repr(self, dec=0):
        if dec < 0:
            ret = '{}.{}'.format(self.__class__.__name__, self.name)
        else:
            ret = super(Enum, self).get_dict_repr(dec)
        return ret


class Dict(dict):
    def __getattr__(self, item):
        try:
            # noinspection PyUnresolvedReferences
            ret = super(Dict, self).__getattr__(item)
        except AttributeError:
            if item in self:
                value = self.get(item)
            else:
                raise AttributeError(
                    "'{}' does not contain attribute '{}'".format(
                        __name__, item))
            ret = value
        return ret


cache = cachez.cache
instance_cache = cachez.instance_cache
clear_instance_cache = cachez.clear_instance_cache


def check_int(value, allow_none=False):
    def is_digit_str():
        return isinstance(value, six.string_types) and str(value).isdigit()

    def is_int():
        return isinstance(value, int)

    if value is None and allow_none:
        ret = None
    else:
        if is_int():
            pass
        elif is_digit_str():
            value = int(value)
        else:
            raise ValueError('"{}" must be an integer.'.format(value))
        ret = int(value)
    return ret


def check_enum(value, enum_class):
    if hasattr(enum_class, 'get_all'):
        get_all_func = getattr(enum_class, 'get_all')
        candidates = get_all_func()
        parsed_enum = enum_class.parse(value)
        if parsed_enum not in candidates:
            raise ValueError('"{}" is not a valid value.  '
                             'Valid values are: {}'.format(value, candidates))
        else:
            value = parsed_enum.value
    else:
        raise ValueError('{} is not a enum.'.format(enum_class))
    return value


def check_text(value):
    if not isinstance(value, six.string_types):
        raise ValueError('"{}" must be text.'.format(value))
    return value


def daemon(func_ref, *args, **kwargs):
    if not callable(func_ref):
        raise ValueError('background only accept callable inputs.')
    t = threading.Thread(target=func_ref, args=args, kwargs=kwargs)
    t.setDaemon(True)
    t.start()
    return t


class WeightedAverage(object):
    def __init__(self, size=5):
        self._data = []
        # linear weight
        self.weight = list(range(size, 0, -1))

    def add(self, *value):
        # the first input is the latest one.
        self._data = list(value[::-1]) + self._data
        self._data = self._data[:self.size]

    @property
    def size(self):
        return len(self.weight)

    def value(self):
        total = 0.0
        weight = 0.0
        ret = 0.0
        for v, w in zip(self._data, self.weight):
            total += v * w
            weight += w
        if weight != 0.0:
            ret = total / weight

        return ret


def _init_lock():
    return threading.Lock()


class SynchronizedDecorator(object):
    lock_map_lock = _init_lock()
    lock_map = {}

    @classmethod
    def synchronized(cls, obj=None):
        """ synchronize on obj if obj is supplied.

        :param obj: the obj to lock on.  if none, lock to the function
        :return: return of the func.
        """

        def get_key(f, o):
            if o is None:
                key = hash(f)
            else:
                key = hash(o)
            return key

        def get_lock(f, o):
            key = get_key(f, o)
            if key not in cls.lock_map:
                with cls.lock_map_lock:
                    if key not in cls.lock_map:
                        cls.lock_map[key] = _init_lock()
            return cls.lock_map[key]

        def wrap(f):
            @functools.wraps(f)
            def new_func(*args, **kw):
                with get_lock(f, obj):
                    return f(*args, **kw)

            return new_func

        return wrap


synchronized = SynchronizedDecorator.synchronized


def const_seconds(value):
    return value


def to_wait(_):
    return const_seconds(30)


retry_per_30_s = partial(retry, wait=to_wait, limit=2)


def _var(func, name, value, *param):
    if value is not None:
        if name is not None:
            ret = [name, func(value, *param)]
        else:
            ret = [func(value, *param)]
    else:
        ret = []
    return ret


text_var = functools.partial(_var, check_text)
int_var = functools.partial(_var, check_int)
enum_var = functools.partial(_var, check_enum)
yes_no_var = functools.partial(_var, lambda b: 'yes' if b else 'no')


class Credential(object):
    def __init__(self, user=None, password=None):
        self.user = user
        self.password = password


def get_clz_from_module(module_name, clz_name):
    ret = None
    if module_name not in sys.modules:
        __import__(module_name)
    module = sys.modules[module_name]
    if hasattr(module, clz_name):
        ret = getattr(module, clz_name)
    return ret


def is_valid(value):
    return value is not None and value != 'N/A' and len(value) > 0


def get_local_folder():
    ret = path.join(path.expanduser('~'), '.storops')
    assure_folder(ret)
    return ret


def assure_folder(folder):
    if not path.exists(folder):
        try:
            makedirs(folder)
        except OSError as e:
            # ignore existing error
            if e.errno != errno.EEXIST:
                raise


def get_file_size(full_path):
    stat_info = stat(full_path)
    return stat_info.st_size


def get_lock_file(name):
    lock_folder = path.join(get_local_folder(), 'file_lock')
    assure_folder(lock_folder)
    return path.join(lock_folder, name)


def get_data_file(name):
    data_folder = get_local_folder()
    assure_folder(data_folder)
    return path.join(data_folder, name)


def round_it(n_digits=3):
    def inner(func):
        @six.wraps(func)
        def _inner(*args, **kwargs):
            value = func(*args, **kwargs)
            return round(value, n_digits)

        return _inner

    return inner


round_3 = round_it(3)


def allow_omit_parentheses(func):
    @six.wraps(func)
    def inner(*args, **kwargs):
        if len(args) == 1 and inspect.isfunction(args[0]):
            # Decorator are used without parentheses, this
            # decorator add the the parentheses
            return func()(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    return inner


class RepeatedTimer(object):
    """ Timer that execute tasks repeatedly

    Referenced from MestreLion's answer on stackoverflow:
    http://stackoverflow.com/questions/2398661/schedule-a-repeating-event-in-python-3
    """

    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.function = function
        self.interval = interval
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self, as_daemon=True):
        if not self.is_running:
            self.is_running = True
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.setDaemon(as_daemon)
            self._timer.start()

    def stop(self):
        if self._timer.is_alive():
            log.info('stop timer for {}.'.format(self.function))
        self._timer.cancel()
        self.is_running = False

    def is_daemon(self):
        return self._timer.isDaemon()

    def __del__(self):
        self.stop()


def all_not_none(*items):
    return all(map(lambda item: item is not None, items))


def all_not_nan(*items):
    return all(map(lambda item: not math.isnan(item), items))
