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
from __future__ import unicode_literals, division

import inspect
import math
import os
import sys
from functools import reduce

from storops.lib.common import cache, all_not_none, allow_omit_parentheses
from storops.lib.metric import MetricConfigList, MetricConfigParser, \
    CalculatorMetaInfo

__author__ = 'Cedric Zhuang'


def get_counter(props):
    if isinstance(props, (list, tuple, set)):
        if len(props) != 1:
            raise ValueError('takes in one and only one property.')
        props = next(iter(props))
    return props


NaN = float('nan')


def isnan(value):
    return math.isnan(value)


def is_valid(value):
    return value is not None and not isnan(value)


def add(op1, op2):
    ret = 0.0
    if is_valid(op1):
        ret += op1
    if is_valid(op2):
        ret += op2
    return ret


def minus(op1, op2):
    if all_not_none(op1, op2):
        ret = op1 - op2
    else:
        ret = NaN
    return ret


def mul(op1, op2):
    if all_not_none(op1, op2):
        ret = op1 * op2
    else:
        ret = NaN
    return ret


def div(op1, op2):
    ret = NaN
    if all_not_none(op1, op2):
        if op1 == 0:
            ret = 0.0
        elif op2 != 0:
            ret = op1 / op2
    return ret


def round_60(value):
    """ round the number to the multiple of 60

    Say a random value is represented by: 60 * n + r
    n is an integer and r is an integer between 0 and 60.
    if r < 30, the result is 60 * n.
    otherwise, the result is 60 * (n + 1)

    The use of this function is that the counter refreshment on
    VNX is always 1 minute.  So the delta time between samples of
    counters must be the multiple of 60.
    :param value: the value to be rounded.
    :return: result
    """
    t = 60
    if value is not None:
        r = value % t
        if r > t / 2:
            ret = value + (t - r)
        else:
            ret = value - r
    else:
        ret = NaN
    return ret


@allow_omit_parentheses
def instance_stats_calculator(per_second=False):
    def decorator(func):
        def wrapper(prev, curr, obj, counters):
            prev_rsc = prev.get_rsc(obj)
            curr_rsc = curr.get_rsc(obj)

            if all_not_none(prev_rsc, curr_rsc):
                ret = func(prev_rsc, curr_rsc, counters)
                if per_second:
                    dt = round_60(curr.delta_seconds(prev))
                    ret = div(ret, dt)
            else:
                ret = NaN
            return ret

        return wrapper

    return decorator


@instance_stats_calculator
def stats_total(prev, curr, counters):
    return reduce(add, (getattr(curr, counter) for counter in counters), 0)


@instance_stats_calculator
def utilization(prev, curr, counters):
    """ calculate the utilization

    delta_busy = curr.busy - prev.busy
    delta_idle = curr.idle - prev.idle
    utilization = delta_busy / (delta_busy + delta_idle)

    :param prev: previous resource
    :param curr: current resource
    :param counters: list of two, busy ticks and idle ticks
    :return: value, NaN if invalid.
    """
    busy_prop, idle_prop = counters

    pb = getattr(prev, busy_prop)
    pi = getattr(prev, idle_prop)

    cb = getattr(curr, busy_prop)
    ci = getattr(curr, idle_prop)

    db = minus(cb, pb)
    di = minus(ci, pi)

    return mul(div(db, add(db, di)), 100)


def aggregated_sum(rsc_list, counters):
    counter = get_counter(counters)
    return reduce(add, getattr(rsc_list, counter), 0.0)


@instance_stats_calculator(per_second=True)
def delta_ps(prev, curr, counters):
    """ calculate the delta per second of one counter

    formula: (curr - prev) / delta_time
    :param prev: previous resource
    :param curr: current resource
    :param counters: the counter to do delta and per second, one only
    :return: value, NaN if invalid.
    """
    counter = get_counter(counters)

    pv = getattr(prev, counter)
    cv = getattr(curr, counter)
    return minus(cv, pv)


@instance_stats_calculator
def io_size_kb(prev, curr, counters):
    """ calculate the io size based on bandwidth and throughput

    formula: average_io_size = bandwidth / throughput
    :param prev: prev resource, not used
    :param curr: current resource
    :param counters: two stats, bandwidth in MB and throughput count
    :return: value, NaN if invalid
    """
    bw_stats, io_stats = counters
    size_mb = div(getattr(curr, bw_stats), getattr(curr, io_stats))
    return mul(size_mb, 1024)


def self_io_size_kb(obj, counters):
    left, right = counters
    return mul(div(getattr(obj, left), getattr(obj, right)), 1024)


def block_to_mbps(prev, curr, obj, counters):
    return delta_ps(prev, curr, obj, counters) * 512 / 2 ** 20


def kb_to_mbps(prev, curr, obj, counters):
    return delta_ps(prev, curr, obj, counters) / 2 ** 10


@cache
def _module_functions():
    return dict(inspect.getmembers(sys.modules[__name__]))


class VNXMetricConfig(object):
    def __init__(self, config):
        self.name = config.get('name')
        self.calculator = self._get_calculator(config)
        self.counters = config.get('counters')
        self.aggregated_from = config.get('aggregated_from')

    @staticmethod
    def _get_calculator(config):
        calc_name = config.get('calculator')
        if not calc_name:
            ret = delta_ps
        else:
            ret = _module_functions().get(calc_name)
        return ret

    def is_aggregated_stats(self):
        return self.aggregated_from is not None


class VNXMetricConfigList(MetricConfigList):
    @classmethod
    def init_metric_config(cls, raw_config):
        return VNXMetricConfig(raw_config)


class VNXMetricConfigParser(MetricConfigParser):
    @classmethod
    def get_config(cls, name):
        name = cls._get_clz_name(name)
        return VNXMetricConfigList(cls._read_configs().get(name))

    @classmethod
    def get_folder(cls):
        return os.path.dirname(inspect.getfile(cls))


class VNXCalculatorMetaInfo(CalculatorMetaInfo):
    def get_config_parser(self):
        return VNXMetricConfigParser()

    def get_metric_value(self, clz, metric_name, cli, obj=None):
        if not hasattr(cli, 'curr_counter'):
            raise ValueError('cli should has "curr_counter" attribute.')
        if not hasattr(cli, 'prev_counter'):
            raise ValueError('cli should has "prev_counter" attribute.')

        config = self.get_config(clz).get_metric_config(metric_name)
        if config.is_aggregated_stats():
            ret = self._get_aggregated_stats(config, obj)
        else:
            ret = self._get_calculated_stats(cli, config, obj)
        return ret

    @staticmethod
    def _get_calculated_stats(cli, config, obj):
        prev = cli.prev_counter
        curr = cli.curr_counter
        if all_not_none(prev, curr):
            ret = config.calculator(prev, curr, obj, config.counters)
        else:
            ret = NaN
        return ret

    @staticmethod
    def _get_aggregated_stats(config, obj):
        if 'self' in config.aggregated_from:
            ret = config.calculator(obj, config.counters)
        else:
            rsc_list = getattr(obj, config.aggregated_from)
            if rsc_list is None:
                rsc_list = []
            ret = config.calculator(rsc_list, config.counters)
        return ret


calculators = VNXCalculatorMetaInfo()
