# coding=utf-8
# Copyright (c) 2016 EMC Corporation.
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
from __future__ import unicode_literals, division

import inspect
import os
import sys

import six

from storops.lib.common import cache, all_not_none
from storops.lib.metric import CalculatorMetaInfo, MetricConfigParser, \
    MetricConfigList

__author__ = 'Cedric Zhuang'


class IdValues(object):
    NaN = float('nan')

    def __init__(self, data=None):
        if data is None:
            data = {}
        self._data = data

    def __sub__(self, other):
        if other is None:
            ret = self
        else:
            ret = self + (-other)
        return ret

    def __rsub__(self, other):
        if other is None:
            ret = -self
        else:
            ret = other + (-self)
        return ret

    def __neg__(self):
        return IdValues({k: -v for k, v in self._data.items()})

    @staticmethod
    def _add(op1, op2):
        if op1 is None:
            r = op2
        elif op2 is None:
            r = op1
        else:
            r = op1 + op2
        return r

    def __add__(self, other):
        if other is not None:
            defaults = 0
            op = self._add

            ret = self._apply_op(defaults, op, other)
        else:
            ret = self.copy()
        return ret

    def _apply_op(self, defaults, op, other):
        if isinstance(other, IdValues):
            keys = self.keys_union(other)
            ret = IdValues(
                {k: op(self.get(k, defaults), other.get(k, defaults))
                 for k in keys})
        else:
            ret = IdValues({k: op(v, other)
                            for k, v in self._data.items()})
        return ret

    def keys_union(self, other):
        return set(other.keys()).union(set(self.keys()))

    def __radd__(self, other):
        return self.__add__(other)

    def __truediv__(self, other):
        return self.__div__(other)

    @classmethod
    def _div(cls, op1, op2):
        if op1 == 0:
            r = 0
        elif op1 is None or op2 is None or op2 == 0:
            r = cls.NaN
        else:
            r = op1 / op2
        return r

    def __div__(self, other):
        return self._apply_op(self.NaN, self._div, other)

    def __rtruediv__(self, other):
        return IdValues({k: self._div(other, v)
                         for k, v in self._data.items()})

    def __rdiv__(self, other):
        return self.__rtruediv__(other)

    @staticmethod
    def _mul(op1, op2):
        if op1 is None:
            r = op2
        elif op2 is None:
            r = op1
        else:
            r = op1 * op2
        return r

    def __mul__(self, other):
        if other is not None:
            ret = self._apply_op(1, self._mul, other)
        else:
            ret = self.copy()
        return ret

    def __rmul__(self, other):
        return self.__mul__(other)

    def copy(self):
        return IdValues({k: v for k, v in self._data.items()})

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
        return self._data.get(item, self.NaN)

    def keys(self):
        return self._data.keys()

    def get(self, k, default=None):
        return self._data.get(k, default)

    def set(self, k, v):
        self._data[k] = v

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self._data)

    def __repr__(self):
        return str(self)


_BLOCK_SIZE = 512


def metric_calculator(f):
    def wrapper(path, prev, curr, obj_id=None):
        ret = f(path, prev, curr)
        if obj_id is not None:
            ret = ret[obj_id]
        return ret

    return wrapper


@metric_calculator
def delta_ps(path, prev, curr):
    path = only_one_path(path)

    if all_not_none(prev, curr):
        prev_counter = prev.by_path(path)
        curr_counter = curr.by_path(path)
    else:
        prev_counter = None
        curr_counter = None

    if all_not_none(prev_counter, curr_counter):
        delta = curr_counter.sum_sp() - prev_counter.sum_sp()
        ret = delta / curr.diff_seconds(prev)
    else:
        ret = IdValues()
    return ret


@metric_calculator
def total_delta_ps(path, prev, curr):
    if len(path) != 2:
        raise ValueError('takes in "reads" and "writes" counter.')

    read_path, write_path = path
    return delta_ps(read_path, prev, curr) + delta_ps(write_path, prev, curr)


def only_one_path(path):
    if isinstance(path, (list, tuple, set)):
        if len(path) != 1:
            raise ValueError('takes in one and only one path.')
        path = next(iter(path))
    return path


@metric_calculator
def mb_ps_by_block(path, prev, curr):
    return delta_ps(path, prev, curr) * _BLOCK_SIZE / (2.0 ** 20)


@metric_calculator
def mb_ps_by_byte(path, prev, curr):
    return delta_ps(path, prev, curr) / (2.0 ** 20)


@metric_calculator
def busy_idle_util(path, prev, curr):
    if len(path) != 2:
        raise ValueError('takes in "busy" and "idle" counter.')

    busy_path, idle_path = path
    if all_not_none(prev, curr):
        prev_busy = prev.by_path(busy_path)
        prev_idle = prev.by_path(idle_path)
        curr_busy = curr.by_path(busy_path)
        curr_idle = curr.by_path(idle_path)

        delta_busy = curr_busy.sum_sp() - prev_busy.sum_sp()
        delta_idle = curr_idle.sum_sp() - prev_idle.sum_sp()
        ret = delta_busy * 100 / (delta_idle + delta_busy)
    else:
        ret = IdValues()
    return ret


def _io_ps(path, prev, curr, attr):
    path = only_one_path(path)

    if all_not_none(prev, curr):
        prev_counter = prev.by_path(path)
        curr_counter = curr.by_path(path)
    else:
        prev_counter = None
        curr_counter = None

    if all_not_none(prev_counter, curr_counter):
        delta = getattr(curr_counter, attr) - getattr(prev_counter, attr)
        ret = delta / curr.diff_seconds(prev)
    else:
        ret = IdValues()
    return ret


@metric_calculator
def sp_delta_ps(path, prev, curr):
    attr = 'sp_values'
    return _io_ps(path, prev, curr, attr)


def _total_io_ps(path, prev, curr, err_msg, func):
    if len(path) != 2:
        raise ValueError(err_msg)

    part1, part2 = path
    return func(part1, prev, curr) + func(part2, prev, curr)


@metric_calculator
def sp_total_delta_ps(path, prev, curr):
    err_msg = 'takes in "reads" and "writes" counter.'
    return _total_io_ps(path, prev, curr, err_msg, sp_delta_ps)


@metric_calculator
def sp_mb_ps_by_byte(path, prev, curr):
    return sp_delta_ps(path, prev, curr) / (2.0 ** 20)


@metric_calculator
def sp_mb_ps_by_block(path, prev, curr):
    return sp_delta_ps(path, prev, curr) * _BLOCK_SIZE / (2.0 ** 20)


@metric_calculator
def sp_busy_idle_util(path, prev, curr):
    if len(path) != 2:
        raise ValueError('takes in "busy" and "idle" counter.')

    return _sp_pct(path, curr, prev)


@metric_calculator
def sp_hit_ratio(path, prev, curr):
    if len(path) != 2:
        raise ValueError('takes in "hit" and "miss" counter.')

    return _sp_pct(path, curr, prev)


@metric_calculator
def sp_fact(path, _, curr):
    path = only_one_path(path)
    return curr.by_path(path).sp_values


def _sp_pct(path, curr, prev):
    part1, part2 = path
    if all_not_none(prev, curr):
        prev_part1 = prev.by_path(part1)
        prev_part2 = prev.by_path(part2)
        curr_part1 = curr.by_path(part1)
        curr_part2 = curr.by_path(part2)

        delta_part1 = curr_part1.sp_values - prev_part1.sp_values
        delta_part2 = curr_part2.sp_values - prev_part2.sp_values
        ret = delta_part1 * 100 / (delta_part2 + delta_part1)
    else:
        ret = IdValues()
    return ret


@metric_calculator
def sp_sum_values(path, _, curr):
    path = only_one_path(path)
    return curr.by_path(path).sp_sum_values


@metric_calculator
def sp_io_rate(path, prev, curr):
    attr = 'sp_sum_values'
    return _io_ps(path, prev, curr, attr)


@metric_calculator
def system_delta_ps(path, prev, curr):
    attr = 'sum_sp_values'
    return _io_ps(path, prev, curr, attr)


@metric_calculator
def system_total_delta_ps(path, prev, curr):
    err_msg = 'takes in "reads" and "writes" counter.'
    return _total_io_ps(path, prev, curr, err_msg, system_delta_ps)


@metric_calculator
def disk_response_time(path, prev, curr):
    if len(path) != 5:
        raise ValueError(
            'takes in "busyTicks", "sumArrivalQueueLength", "reads", '
            '"writes" and "coreCount" counter.')

    busy_tick_path, sum_arr_ql_path, read_path, write_path, core_count_path = \
        path
    if all_not_none(prev, curr):
        prev_busy_tick = prev.by_path(busy_tick_path)
        prev_sum_arr_ql = prev.by_path(sum_arr_ql_path)
        prev_read = prev.by_path(read_path)
        prev_write = prev.by_path(write_path)
        prev_core_count = prev.by_path(core_count_path)

        curr_busy_tick = curr.by_path(busy_tick_path)
        curr_sum_arr_ql = curr.by_path(sum_arr_ql_path)
        curr_read = curr.by_path(read_path)
        curr_write = curr.by_path(write_path)
        curr_core_count = curr.by_path(core_count_path)

        delta_busy_tick = curr_busy_tick.sum_sp() - prev_busy_tick.sum_sp()
        delta_sum_arr_ql = curr_sum_arr_ql.sum_sp() - prev_sum_arr_ql.sum_sp()
        delta_read = curr_read.sum_sp() - prev_read.sum_sp()
        delta_write = curr_write.sum_sp() - prev_write.sum_sp()

        delta_read_core_count = curr_read.combine_numeric_values(
            curr_core_count) - prev_read.combine_numeric_values(
            prev_core_count)
        delta_write_core_count = curr_write.combine_numeric_values(
            curr_core_count) - prev_write.combine_numeric_values(
            prev_core_count)

        ret = delta_busy_tick * delta_sum_arr_ql / (
            (delta_read + delta_write) *
            (delta_read_core_count + delta_write_core_count))

    else:
        ret = IdValues()

    return ret


def _queue_length(path, prev, curr, err_msg, func):
    if len(path) != 3:
        raise ValueError(err_msg)

    part1, part2, part3 = path
    if all_not_none(prev, curr):
        prev_part1 = prev.by_path(part1)
        prev_part2 = prev.by_path(part2)
        prev_part3 = prev.by_path(part3)

        curr_part1 = curr.by_path(part1)
        curr_part2 = curr.by_path(part2)
        curr_part3 = curr.by_path(part3)

        delta_part1 = curr_part1.sum_sp() - prev_part1.sum_sp()
        delta_part2 = curr_part2.sum_sp() - prev_part2.sum_sp()
        delta_part3 = curr_part3.sum_sp() - prev_part3.sum_sp()

        ret = func(delta_part1, delta_part2, delta_part3)

    else:
        ret = IdValues()

    return ret


@metric_calculator
def disk_queue_length(path, prev, curr):
    err_msg = 'takes in "sumArrivalQueueLength", "reads" and "writes" counter.'
    return _queue_length(path, prev, curr, err_msg,
                         lambda x, y, z: x / (y + z))


@metric_calculator
def lun_response_time(path, prev, curr):
    err_msg = 'takes in "totalIoTime", "reads" and "writes" counter.'
    return _queue_length(path, prev, curr, err_msg,
                         lambda x, y, z: x / (y + z))


@metric_calculator
def lun_queue_length(path, prev, curr):
    err_msg = 'takes in "currentIOCount", "busyTime" and "idleTime" counter.'
    return _queue_length(path, prev, curr, err_msg,
                         lambda x, y, z: x * y / (y + z))


def _byte_rate(path, prev, curr, err_msg, attr):
    if len(path) != 2:
        raise ValueError(err_msg)

    part1, part2 = path
    if all_not_none(prev, curr):
        delta = getattr(curr.by_path(part1), attr)(
            curr.by_path(part2)) - getattr(prev.by_path(part1), attr)(
            prev.by_path(part2))
        ret = delta / curr.diff_seconds(prev)
    else:
        ret = IdValues()

    return ret


@metric_calculator
def byte_rate(path, prev, curr):
    err_msg = 'takes in "Blocks" and "blockSize" counter.'
    attr = 'combine_numeric_values'
    return _byte_rate(path, prev, curr, err_msg, attr)


@metric_calculator
def sp_byte_rate(path, prev, curr):
    err_msg = 'takes in "Blocks" and "blockSize" counter.'
    attr = 'combine_sp_values'
    return _byte_rate(path, prev, curr, err_msg, attr)


@metric_calculator
def system_byte_rate(path, prev, curr):
    err_msg = 'takes in "Blocks" and "blockSize" counter.'
    attr = 'sum_combined_sp_values'
    return _byte_rate(path, prev, curr, err_msg, attr)


def _total_byte_rate(path, prev, curr, err_msg, func):
    if len(path) != 3:
        raise ValueError(err_msg)

    part1, part2, part3 = path
    return func((part1, part3), prev, curr) + func((part2, part3), prev, curr)


@metric_calculator
def total_byte_rate(path, prev, curr):
    err_msg = 'takes in "readBlocks", "writeBlocks" and "blockSize" counter.'
    return _total_byte_rate(path, prev, curr, err_msg, byte_rate)


@metric_calculator
def sp_total_byte_rate(path, prev, curr):
    err_msg = 'takes in "readBlocks", "writeBlocks" and "blockSize" counter.'
    return _total_byte_rate(path, prev, curr, err_msg, sp_byte_rate)


@metric_calculator
def system_total_byte_rate(path, prev, curr):
    err_msg = 'takes in "readBlocks", "writeBlocks" and "blockSize" counter.'
    return _total_byte_rate(path, prev, curr, err_msg, system_byte_rate)


@cache
def _module_functions():
    return dict(inspect.getmembers(sys.modules[__name__]))


class UnityMetricConfig(object):
    def __init__(self, config):
        self.name = config.get('name')
        paths = self._get_paths(config)
        self.paths = paths
        self.calculator = self._get_calculator(config)

    @staticmethod
    def _get_calculator(config):
        calc_name = config.get('calculator')
        if calc_name is None:
            ret = delta_ps
        else:
            ret = _module_functions().get(calc_name)
        return ret

    @staticmethod
    def _get_paths(config):
        paths = config.get('paths')
        if isinstance(paths, six.string_types):
            paths = [paths]
        return paths


class UnityMetricConfigList(MetricConfigList):
    def init_metric_config(self, raw_config):
        return UnityMetricConfig(raw_config)


class UnityMetricConfigParser(MetricConfigParser):
    @classmethod
    def get_folder(cls):
        return os.path.dirname(inspect.getfile(cls))

    @classmethod
    def get_config(cls, name):
        name = cls._get_clz_name(name)
        return UnityMetricConfigList(cls._read_configs().get(name))

    @classmethod
    @cache
    def paths(cls, clz_list=None):
        if clz_list is None:
            clz_list = cls._read_configs().keys()

        return [path for config in map(cls.get_config, clz_list)
                for path in config.paths()]


class UnityCalculatorMetaInfo(CalculatorMetaInfo):
    def get_config_parser(self):
        return UnityMetricConfigParser()

    def get_metric_value(self, clz, metric_name, cli, obj=None):
        if not hasattr(cli, 'curr_counter'):
            raise ValueError('cli should has "curr_counter" attribute.')
        if not hasattr(cli, 'prev_counter'):
            raise ValueError('cli should has "prev_counter" attribute.')

        config = self.get_config(clz).get_metric_config(metric_name)
        return config.calculator(config.paths, cli.prev_counter,
                                 cli.curr_counter, obj)

    def get_all_paths(self, clz_list=None):
        if clz_list is not None:
            clz_list = tuple(clz_list)
        return self._metric_config.paths(clz_list)


calculators = UnityCalculatorMetaInfo()
