# coding=utf-8
# Copyright (c) 2020 Dell Inc. or its subsidiaries.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from __future__ import unicode_literals

from unittest import TestCase

import ddt
from hamcrest import assert_that, equal_to, raises, calling

from storops.unity.enums import FilesystemSnapAccessTypeEnum, \
    ScheduleTypeEnum, DayOfWeekEnum, ScheduleVersionEnum
from storops.unity.resource.snap_schedule import UnitySnapSchedule, \
    UnitySnapScheduleRule, UnitySnapScheduleList
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Ryan Liang'


@ddt.ddt
class UnitySnapScheduleRuleTest(TestCase):
    @ddt.data(
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': None, 'days_of_week': None, 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'expected':
             {'type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
              'hours': None, 'daysOfWeek': None, 'daysOfMonth': None,
              'interval': None, 'isAutoDelete': None, 'retentionTime': None,
              'accessType': None, }},
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': 0,
         'hours': [8], 'days_of_week': [DayOfWeekEnum.MONDAY],
         'days_of_month': [10],
         'interval': 15, 'is_auto_delete': True, 'retention_time': 3600,
         'access_type': FilesystemSnapAccessTypeEnum.CHECKPOINT,
         'expected':
             {'type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': 0,
              'hours': [8], 'daysOfWeek': [DayOfWeekEnum.MONDAY],
              'daysOfMonth': [10],
              'interval': 15, 'isAutoDelete': True, 'retentionTime': 3600,
              'accessType': FilesystemSnapAccessTypeEnum.CHECKPOINT, }},
    )
    @ddt.unpack
    def test_to_embedded(self, schedule_type, minute, hours, days_of_week,
                         days_of_month, interval, is_auto_delete,
                         retention_time, access_type, expected):
        assert_that(
            UnitySnapScheduleRule.to_embedded(schedule_type, minute=minute,
                                              hours=hours,
                                              days_of_week=days_of_week,
                                              days_of_month=days_of_month,
                                              interval=interval,
                                              is_auto_delete=is_auto_delete,
                                              retention_time=retention_time,
                                              access_type=access_type),
            equal_to(expected))

    @ddt.data(
        {'schedule_type': None, 'minute': None,
         'hours': None, 'days_of_week': None, 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'None is not allowed here for ScheduleTypeEnum'},
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': -1,
         'hours': None, 'days_of_week': None, 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg':
             'minute in UnitySnapScheduleRule should be \[0, 59\].'},  # noqa
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': 60,
         'hours': None, 'days_of_week': None, 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg':
             'minute in UnitySnapScheduleRule should be \[0, 59\].'},  # noqa
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': 10, 'days_of_week': None, 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'hours in UnitySnapScheduleRule should be a list '
                      'and not an empty list.'},
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': [], 'days_of_week': None, 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'hours in UnitySnapScheduleRule should be a list '
                      'and not an empty list.'},
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': [-1, 10], 'days_of_week': None, 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'each value of hours in UnitySnapScheduleRule should be '
                      '\[0, 23\].'},  # noqa
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': [24, 10], 'days_of_week': None, 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'each value of hours in UnitySnapScheduleRule should be '
                      '\[0, 23\].'},  # noqa
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': None, 'days_of_week': 1, 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'days_of_week in UnitySnapScheduleRule should be a list '
                      'and not an empty list.'},
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': None, 'days_of_week': [], 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'days_of_week in UnitySnapScheduleRule should be a list '
                      'and not an empty list.'},
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': None, 'days_of_week': [0, 3], 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': '0 is not an instance of DayOfWeekEnum.'},
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': None, 'days_of_week': [8, 3], 'days_of_month': None,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': '8 is not an instance of DayOfWeekEnum.'},
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': None, 'days_of_week': None, 'days_of_month': 1,
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'days_of_month in UnitySnapScheduleRule should be a '
                      'list and not an empty list.'},
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': None, 'days_of_week': None, 'days_of_month': [],
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'days_of_month in UnitySnapScheduleRule should be a '
                      'list and not an empty list.'},
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': None, 'days_of_week': None, 'days_of_month': [0, 3],
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'each value of days_of_month in UnitySnapScheduleRule '
                      'should be \[1, 31\].'},  # noqa
        {'schedule_type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': None,
         'hours': None, 'days_of_week': None, 'days_of_month': [32, 3],
         'interval': None, 'is_auto_delete': None, 'retention_time': None,
         'access_type': None,
         'error_msg': 'each value of days_of_month in UnitySnapScheduleRule '
                      'should be \[1, 31\].'},  # noqa
    )
    @ddt.unpack
    def test_to_embedded_value_error(self, schedule_type, minute, hours,
                                     days_of_week, days_of_month, interval,
                                     is_auto_delete, retention_time,
                                     access_type, error_msg):
        assert_that(
            calling(UnitySnapScheduleRule.to_embedded).with_args(
                schedule_type, minute=minute, hours=hours,
                days_of_week=days_of_week, days_of_month=days_of_month,
                interval=interval, is_auto_delete=is_auto_delete,
                retention_time=retention_time, access_type=access_type),
            raises(ValueError, error_msg))

    @ddt.data(
        {'hour_interval': 3, 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'expected':
             {'type': ScheduleTypeEnum.N_HOURS_AT_MM, 'minute': 0,
              'hours': None, 'daysOfWeek': None,
              'daysOfMonth': None,
              'interval': 3, 'isAutoDelete': None, 'retentionTime': None,
              'accessType': None}},
        {'hour_interval': 3, 'minute': 30,
         'is_auto_delete': True, 'retention_time': 3600,
         'access_type': FilesystemSnapAccessTypeEnum.CHECKPOINT,
         'expected':
             {'type': ScheduleTypeEnum.N_HOURS_AT_MM, 'minute': 30,
              'hours': None, 'daysOfWeek': None,
              'daysOfMonth': None,
              'interval': 3, 'isAutoDelete': True, 'retentionTime': 3600,
              'accessType': FilesystemSnapAccessTypeEnum.CHECKPOINT}},
    )
    def test_every_n_hours(self, kwargs):
        hour_interval = kwargs.pop('hour_interval')
        expected = kwargs.pop('expected')
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        assert_that(UnitySnapScheduleRule.every_n_hours(hour_interval,
                                                        **kwargs),
                    equal_to(expected))

    @ddt.data(
        {'hours': [0, 12], 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'expected':
             {'type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': 0,
              'hours': [0, 12], 'daysOfWeek': None,
              'daysOfMonth': None,
              'interval': 1, 'isAutoDelete': None, 'retentionTime': None,
              'accessType': None}},
        {'hours': [0, 12], 'minute': 30,
         'is_auto_delete': True, 'retention_time': 3600,
         'access_type': FilesystemSnapAccessTypeEnum.CHECKPOINT,
         'expected':
             {'type': ScheduleTypeEnum.DAY_AT_HHMM, 'minute': 30,
              'hours': [0, 12], 'daysOfWeek': None,
              'daysOfMonth': None,
              'interval': 1, 'isAutoDelete': True, 'retentionTime': 3600,
              'accessType': FilesystemSnapAccessTypeEnum.CHECKPOINT}},
    )
    def test_every_day(self, kwargs):
        hours = kwargs.pop('hours')
        expected = kwargs.pop('expected')
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        assert_that(UnitySnapScheduleRule.every_day(hours,
                                                    **kwargs),
                    equal_to(expected))

    @ddt.data(
        {'hours': 12, 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'error_msg': 'hours of UnitySnapScheduleRule every_day rule should '
                      'be a list.'},
        {'hours': [], 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'error_msg': 'hours of UnitySnapScheduleRule every_day rule cannot '
                      'be empty list.'}
    )
    def test_every_day_value_error(self, kwargs):
        hours = kwargs.pop('hours')
        error_msg = kwargs.pop('error_msg')
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        assert_that(
            calling(UnitySnapScheduleRule.every_day).with_args(hours,
                                                               **kwargs),
            raises(ValueError, error_msg))

    @ddt.data(
        {'day_interval': 3, 'hour': 0, 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'expected':
             {'type': ScheduleTypeEnum.N_DAYS_AT_HHMM, 'minute': 0,
              'hours': [0], 'daysOfWeek': None,
              'daysOfMonth': None,
              'interval': 3, 'isAutoDelete': None, 'retentionTime': None,
              'accessType': None}},
        {'day_interval': 3, 'hour': 0, 'minute': 30,
         'is_auto_delete': True, 'retention_time': 3600,
         'access_type': FilesystemSnapAccessTypeEnum.CHECKPOINT,
         'expected':
             {'type': ScheduleTypeEnum.N_DAYS_AT_HHMM, 'minute': 30,
              'hours': [0], 'daysOfWeek': None,
              'daysOfMonth': None,
              'interval': 3, 'isAutoDelete': True, 'retentionTime': 3600,
              'accessType': FilesystemSnapAccessTypeEnum.CHECKPOINT}},
    )
    def test_every_n_days(self, kwargs):
        day_interval = kwargs.pop('day_interval')
        expected = kwargs.pop('expected')
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        assert_that(UnitySnapScheduleRule.every_n_days(day_interval,
                                                       **kwargs),
                    equal_to(expected))

    @ddt.data(
        {'days_of_week': [DayOfWeekEnum.TUESDAY, DayOfWeekEnum.THURSDAY],
         'hour': None, 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'expected':
             {'type': ScheduleTypeEnum.SELDAYS_AT_HHMM, 'minute': 0,
              'hours': [0],
              'daysOfWeek': [DayOfWeekEnum.TUESDAY, DayOfWeekEnum.THURSDAY],
              'daysOfMonth': None,
              'interval': None, 'isAutoDelete': None, 'retentionTime': None,
              'accessType': None}},
        {'days_of_week': [DayOfWeekEnum.TUESDAY, DayOfWeekEnum.THURSDAY],
         'hour': 12, 'minute': 30,
         'is_auto_delete': True, 'retention_time': 3600,
         'access_type': FilesystemSnapAccessTypeEnum.CHECKPOINT,
         'expected':
             {'type': ScheduleTypeEnum.SELDAYS_AT_HHMM, 'minute': 30,
              'hours': [12],
              'daysOfWeek': [DayOfWeekEnum.TUESDAY, DayOfWeekEnum.THURSDAY],
              'daysOfMonth': None,
              'interval': None, 'isAutoDelete': True, 'retentionTime': 3600,
              'accessType': FilesystemSnapAccessTypeEnum.CHECKPOINT}},
    )
    def test_every_week(self, kwargs):
        days_of_week = kwargs.pop('days_of_week')
        expected = kwargs.pop('expected')
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        assert_that(UnitySnapScheduleRule.every_week(days_of_week,
                                                     **kwargs),
                    equal_to(expected))

    @ddt.data(
        {'days_of_week': 2, 'hour': None, 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'error_msg': 'days_of_week of UnitySnapScheduleRule every_week rule '
                      'should be a list.'},
        {'days_of_week': [], 'hour': None, 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'error_msg': 'days_of_week of UnitySnapScheduleRule every_week rule '
                      'cannot be empty list.'}
    )
    def test_every_week_value_error(self, kwargs):
        days_of_week = kwargs.pop('days_of_week')
        error_msg = kwargs.pop('error_msg')
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        assert_that(
            calling(UnitySnapScheduleRule.every_week).with_args(days_of_week,
                                                                **kwargs),
            raises(ValueError, error_msg))

    @ddt.data(
        {'days_of_month': [10, 20], 'hour': None, 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'expected':
             {'type': ScheduleTypeEnum.NTH_DAYOFMONTH_AT_HHMM,
              'minute': 0, 'hours': [0],
              'daysOfWeek': None,
              'daysOfMonth': [10, 20],
              'interval': None, 'isAutoDelete': None, 'retentionTime': None,
              'accessType': None}},
        {'days_of_month': [10, 20], 'hour': 12, 'minute': 30,
         'is_auto_delete': True, 'retention_time': 3600,
         'access_type': FilesystemSnapAccessTypeEnum.CHECKPOINT,
         'expected':
             {'type': ScheduleTypeEnum.NTH_DAYOFMONTH_AT_HHMM,
              'minute': 30, 'hours': [12],
              'daysOfWeek': None,
              'daysOfMonth': [10, 20],
              'interval': None, 'isAutoDelete': True, 'retentionTime': 3600,
              'accessType': FilesystemSnapAccessTypeEnum.CHECKPOINT}},
    )
    def test_every_month(self, kwargs):
        days_of_month = kwargs.pop('days_of_month')
        expected = kwargs.pop('expected')
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        assert_that(UnitySnapScheduleRule.every_month(days_of_month,
                                                      **kwargs),
                    equal_to(expected))

    @ddt.data(
        {'days_of_month': 10, 'hour': None, 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'error_msg': 'days_of_month of UnitySnapScheduleRule every_month '
                      'rule should be a list.'},
        {'days_of_month': [], 'hour': None, 'minute': None,
         'is_auto_delete': None, 'retention_time': None, 'access_type': None,
         'error_msg': 'days_of_month of UnitySnapScheduleRule every_month '
                      'rule cannot be empty list.'}
    )
    def test_every_month_value_error(self, kwargs):
        days_of_month = kwargs.pop('days_of_month')
        error_msg = kwargs.pop('error_msg')
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        assert_that(
            calling(UnitySnapScheduleRule.every_month).with_args(days_of_month,
                                                                 **kwargs),
            raises(ValueError, error_msg))


@ddt.ddt
class UnitySnapScheduleTest(TestCase):
    @patch_rest
    def test_properties(self):
        schedule = UnitySnapSchedule(_id='snapSch_1', cli=t_rest())
        assert_that(schedule.existed, equal_to(True))
        assert_that(schedule.version, equal_to(ScheduleVersionEnum.LEGACY))
        assert_that(schedule.name, equal_to('Snapshot Schedule 1'))
        assert_that(schedule.is_default, equal_to(False))
        assert_that(schedule.is_modified, equal_to(False))
        assert_that(str(schedule.modification_time),
                    equal_to('2020-03-17 07:37:56.695000+00:00'))
        assert_that(len(schedule.rules), equal_to(1))
        assert_that(schedule.rules[0].type,
                    equal_to(ScheduleTypeEnum.DAY_AT_HHMM))
        assert_that(len(schedule.rules[0].days_of_week), equal_to(0))
        assert_that(schedule.rules[0].access_type,
                    equal_to(FilesystemSnapAccessTypeEnum.CHECKPOINT))
        assert_that(schedule.rules[0].minute, equal_to(0))
        assert_that(schedule.rules[0].hours, equal_to([4]))
        assert_that(schedule.rules[0].interval, equal_to(1))
        assert_that(schedule.rules[0].is_auto_delete, equal_to(True))
        assert_that(schedule.rules[0].retention_time, equal_to(0))
        assert_that(schedule.is_sync_replicated, equal_to(False))
        assert_that(len(schedule.luns), equal_to(1))
        assert_that(schedule.luns[0].get_id(), equal_to('sv_2'))

    @patch_rest
    def test_get_all(self):
        schedules = UnitySnapScheduleList(cli=t_rest())
        assert_that(schedules[0].existed, equal_to(True))
        assert_that(len(schedules), equal_to(3))

    @ddt.data(
        {'is_sync_replicated': None, 'skip_sync_to_remote_system': None,
         'expected': 'snapSch_4'},
        {'is_sync_replicated': True, 'skip_sync_to_remote_system': True,
         'expected': 'snapSch_5'},
    )
    @patch_rest
    def test_create(self, kwargs):
        expected = kwargs.pop('expected')
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        schedule = UnitySnapSchedule.create(
            t_rest(), 'snap-schedule', [UnitySnapScheduleRule.every_day([12])],
            **kwargs
        )
        assert_that(schedule.get_id(), equal_to(expected))

    @ddt.data(
        {'add_rules': [UnitySnapScheduleRule.every_month([10])],
         'remove_rule_ids': None,
         'skip_sync_to_remote_system': None},
        {'add_rules': None,
         'remove_rule_ids': ['SchedRule_4'],
         'skip_sync_to_remote_system': None},
        {'add_rules': None,
         'remove_rule_ids': None,
         'skip_sync_to_remote_system': True},
    )
    @patch_rest
    def test_modify(self, kwargs):
        schedule = UnitySnapSchedule(_id='snapSch_4', cli=t_rest())
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        resp = schedule.modify(**kwargs)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete(self):
        schedule = UnitySnapSchedule(_id='snapSch_4', cli=t_rest())
        resp = schedule.delete()
        assert_that(resp.is_ok(), equal_to(True))
