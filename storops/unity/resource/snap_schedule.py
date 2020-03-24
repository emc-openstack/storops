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

import logging

from storops.unity.enums import ScheduleTypeEnum, DayOfWeekEnum, \
    FilesystemSnapAccessTypeEnum
from storops.unity.resource import UnityResource, UnityResourceList

__author__ = 'Ryan Liang'

log = logging.getLogger(__name__)


class UnitySnapScheduleRule(UnityResource):
    @staticmethod
    def to_embedded(schedule_type, minute=None, hours=None, days_of_week=None,
                    days_of_month=None, interval=None, is_auto_delete=None,
                    retention_time=None, access_type=None):
        """
        Constructs a `SnapScheduleRule` embedded instance.

        The rule created depends on the value of `schedule_type`. Its value
        could be:
        0. `N_HOURS_AT_MM`, snap every `interval` hours, at `minute`
            past the hour. Supported parameters: `interval` (required),
            `minute` (optional, default 0).
        1. `DAY_AT_HHMM`, specify `hours` as a list of `hour[,...]` to snap one
            or more times each day at `minute` past the hour. Supported
            parameters: `hours` (at least one required), `minute` (optional).
        2. `N_DAYS_AT_HHMM`, snap every `interval` days at the time
            `hours`:`minute`. Supported Parameters: `interval` (required),
            `hours` (optional, exactly one), `minute` (optional).
        3. `SELDAYS_AT_HHMM`, snap on the selected `days_of_week`, at the time
            `hours`:`minute`. Supported parameters: `days_of_week` (at least
            one required), `hours` (optional, default 0), `minute` (optional,
            default 0).
        4. `NTH_DAYOFMONTH_AT_HHMM`, snap on the selected `days_of_month`, at
            the time `hours`:`minute`. Supported parameters: `days_of_month`
            (at least one required), `hours` (optional, default 0), `minute`
            (optional, default 0).
        5. `UNSUPPORTED`.

        :param schedule_type: Type of snapshot schedule rule. Value is
            ScheduleTypeEnum.
        :param minute: Minute frequency for the snapshot schedule rule. Value
            should be [0, 59].
        :param hours: Hourly frequency for the snapshot schedule rule. Each
            value should be [0, 23].
        :param days_of_week: Days of the week for which the snapshot schedule
            rule applies. Each value is DayOfWeekEnum.
        :param days_of_month: Days of the month for which the snapshot schedule
            rule applies. Each value should be [1, 31].
        :param interval: Number of days or hours between snaps, depending on
            the rule type.
        :param is_auto_delete: Indicates whether the system can automatically
            delete the snapshot based on pool automatic-deletion thresholds.
            Values are:
                true - System can delete the snapshot based on pool
                    automatic-deletion thresholds.
                false - System cannot delete the snapshot based on pool
                    automatic-deletion thresholds.
        :param retention_time: (Applies when the value of the is_auto_delete
            attribute is false.) Period of time in seconds for which to keep
            the snapshot.
        :param access_type: For a file system or VMware NFS datastore snapshot
            schedule, indicates whether the snapshot created by the schedule
            has checkpoint or protocol type access. Value is
            FilesystemSnapAccessTypeEnum.
        :return: constructed embedded instance in a dict.
        """
        ScheduleTypeEnum.verify(schedule_type, allow_none=False)
        if minute is not None and (minute < 0 or minute > 59):
            raise ValueError(
                'minute in UnitySnapScheduleRule should be [0, 59].')
        if hours is not None:
            if not isinstance(hours, list) or not hours:
                raise ValueError(
                    'hours in UnitySnapScheduleRule should be a list '
                    'and not an empty list.')
            if any([(hour < 0 or hour > 23) for hour in hours]):
                raise ValueError(
                    'each value of hours in UnitySnapScheduleRule should be '
                    '[0, 23].')
        if days_of_week is not None:
            if not isinstance(days_of_week, list) or not days_of_week:
                raise ValueError(
                    'days_of_week in UnitySnapScheduleRule should be a list '
                    'and not an empty list.')
            for day_of_week in days_of_week:
                DayOfWeekEnum.verify(day_of_week, allow_none=False)

        if days_of_month is not None:
            if not isinstance(days_of_month, list) or not days_of_month:
                raise ValueError(
                    'days_of_month in UnitySnapScheduleRule should be a list '
                    'and not an empty list.')
            if any([(day < 1 or day > 31) for day in days_of_month]):
                raise ValueError(
                    'each value of days_of_month in UnitySnapScheduleRule '
                    'should be [1, 31].')

        FilesystemSnapAccessTypeEnum.verify(access_type)

        return {
            'type': schedule_type,
            'minute': minute,
            'hours': hours,
            'daysOfWeek': days_of_week,
            'daysOfMonth': days_of_month,
            'interval': interval,
            'isAutoDelete': is_auto_delete,
            'retentionTime': retention_time,
            'accessType': access_type,
        }

    @staticmethod
    def every_n_hours(hour_interval, minute=0, is_auto_delete=None,
                      retention_time=None, access_type=None):
        """
        Helper function to construct `N_HOURS_AT_MM` type rule.

        In this rule the snapshot will be taken every `hour_interval` hours,
        at `minute` past the hour.

        :param hour_interval: the interval in hour the snapshot will be taken.
        :param minute: minutes past the hour when the snapshot will be taken.
            Value should be [0, 59], and is 0 by default.
        :param is_auto_delete: Indicates whether the system can automatically
            delete the snapshot based on pool automatic-deletion thresholds.
            Values are:
                true - System can delete the snapshot based on pool
                    automatic-deletion thresholds.
                false - System cannot delete the snapshot based on pool
                    automatic-deletion thresholds.
        :param retention_time: (Applies when the value of the is_auto_delete
            attribute is false.) Period of time in seconds for which to keep
            the snapshot.
        :param access_type: For a file system or VMware NFS datastore snapshot
            schedule, indicates whether the snapshot created by the schedule
            has checkpoint or protocol type access. Value is
            FilesystemSnapAccessTypeEnum.
        :return: constructed embedded instance in a dict.
        """
        return UnitySnapScheduleRule.to_embedded(
            ScheduleTypeEnum.N_HOURS_AT_MM,
            interval=hour_interval,
            minute=minute,
            is_auto_delete=is_auto_delete,
            retention_time=retention_time,
            access_type=access_type,
        )

    @staticmethod
    def every_day(hours, minute=0, is_auto_delete=None, retention_time=None,
                  access_type=None):
        """
        Helper function to construct `DAY_AT_HHMM` type rule.

        In this rule the snapshot will be taken at hours specified by a list of
        `hour[,...]`, and at `minute` past the hour.

        :param hours: a list of `hour[,...]` at which hour the snapshot will be
            taken. Cannot be empty list and each value should be [0, 23].
        :param minute: minutes past the hour when the snapshot will be taken.
            Value should be [0, 59], and is 0 by default.
        :param is_auto_delete: Indicates whether the system can automatically
            delete the snapshot based on pool automatic-deletion thresholds.
            Values are:
                true - System can delete the snapshot based on pool
                    automatic-deletion thresholds.
                false - System cannot delete the snapshot based on pool
                    automatic-deletion thresholds.
        :param retention_time: (Applies when the value of the is_auto_delete
            attribute is false.) Period of time in seconds for which to keep
            the snapshot.
        :param access_type: For a file system or VMware NFS datastore snapshot
            schedule, indicates whether the snapshot created by the schedule
            has checkpoint or protocol type access. Value is
            FilesystemSnapAccessTypeEnum.
        :return: constructed embedded instance in a dict.
        """
        if not isinstance(hours, list):
            raise ValueError(
                'hours of UnitySnapScheduleRule every_day rule should be '
                'a list.')
        if not hours:
            raise ValueError(
                'hours of UnitySnapScheduleRule every_day rule cannot be '
                'empty list.')
        return UnitySnapScheduleRule.to_embedded(
            ScheduleTypeEnum.DAY_AT_HHMM,
            interval=1,  # Every day
            hours=hours,
            minute=minute,
            is_auto_delete=is_auto_delete,
            retention_time=retention_time,
            access_type=access_type,
        )

    @staticmethod
    def every_n_days(day_interval, hour=0, minute=0, is_auto_delete=None,
                     retention_time=None, access_type=None):
        """
        Helper function to construct `N_DAYS_AT_HHMM` type rule.

        In this rule the snapshot will be taken every `day_interval` days at
        the time `hour`:`minute`.

        :param day_interval: the interval in day the snapshot will be taken.
        :param hour: the hour when the snapshot will be taken. Value should be
            [0, 23], and is 0 by default.
        :param minute: minutes past the hour when the snapshot will be taken.
            Value should be [0, 59], and is 0 by default.
        :param is_auto_delete: Indicates whether the system can automatically
            delete the snapshot based on pool automatic-deletion thresholds.
            Values are:
                true - System can delete the snapshot based on pool
                    automatic-deletion thresholds.
                false - System cannot delete the snapshot based on pool
                    automatic-deletion thresholds.
        :param retention_time: (Applies when the value of the is_auto_delete
            attribute is false.) Period of time in seconds for which to keep
            the snapshot.
        :param access_type: For a file system or VMware NFS datastore snapshot
            schedule, indicates whether the snapshot created by the schedule
            has checkpoint or protocol type access. Value is
            FilesystemSnapAccessTypeEnum.
        :return: constructed embedded instance in a dict.
        """
        return UnitySnapScheduleRule.to_embedded(
            ScheduleTypeEnum.N_DAYS_AT_HHMM,
            interval=day_interval,
            hours=[hour],
            minute=minute,
            is_auto_delete=is_auto_delete,
            retention_time=retention_time,
            access_type=access_type,
        )

    @staticmethod
    def every_week(days_of_week, hour=0, minute=0, is_auto_delete=None,
                   retention_time=None, access_type=None):
        """
        Helper function to construct `SELDAYS_AT_HHMM` type rule.

        In this rule the snapshot will be taken on the selected `days_of_week`,
        at the time `hour`:`minute`.

        :param days_of_week: days in every week the snapshot will be taken.
            Cannot be empty list and each value is DayOfWeekEnum.
        :param hour: the hour when the snapshot will be taken. Value should be
            [0, 23], and is 0 by default.
        :param minute: minutes past the hour when the snapshot will be taken.
            Value should be [0, 59], and is 0 by default.
        :param is_auto_delete: Indicates whether the system can automatically
            delete the snapshot based on pool automatic-deletion thresholds.
            Values are:
                true - System can delete the snapshot based on pool
                    automatic-deletion thresholds.
                false - System cannot delete the snapshot based on pool
                    automatic-deletion thresholds.
        :param retention_time: (Applies when the value of the is_auto_delete
            attribute is false.) Period of time in seconds for which to keep
            the snapshot.
        :param access_type: For a file system or VMware NFS datastore snapshot
            schedule, indicates whether the snapshot created by the schedule
            has checkpoint or protocol type access. Value is
            FilesystemSnapAccessTypeEnum.
        :return: constructed embedded instance in a dict.
        """
        if not isinstance(days_of_week, list):
            raise ValueError(
                'days_of_week of UnitySnapScheduleRule every_week rule should '
                'be a list.')
        if not days_of_week:
            raise ValueError(
                'days_of_week of UnitySnapScheduleRule every_week rule cannot '
                'be empty list.')
        return UnitySnapScheduleRule.to_embedded(
            ScheduleTypeEnum.SELDAYS_AT_HHMM,
            days_of_week=days_of_week,
            hours=[hour],
            minute=minute,
            is_auto_delete=is_auto_delete,
            retention_time=retention_time,
            access_type=access_type,
        )

    @staticmethod
    def every_month(days_of_month, hour=0, minute=0, is_auto_delete=None,
                    retention_time=None, access_type=None):
        """
        Helper function to construct `NTH_DAYOFMONTH_AT_HHMM` type rule.

        In this rule the snapshot will be taken on the selected
        `days_of_month`, at the time `hour`:`minute`.

        :param days_of_month: days in every month the snapshot will be taken.
            Cannot be empty list.
        :param hour: the hour when the snapshot will be taken. Value should be
            [0, 23], and is 0 by default.
        :param minute: minutes past the hour when the snapshot will be taken.
            Value should be [0, 59], and is 0 by default.
        :param is_auto_delete: Indicates whether the system can automatically
            delete the snapshot based on pool automatic-deletion thresholds.
            Values are:
                true - System can delete the snapshot based on pool
                    automatic-deletion thresholds.
                false - System cannot delete the snapshot based on pool
                    automatic-deletion thresholds.
        :param retention_time: (Applies when the value of the is_auto_delete
            attribute is false.) Period of time in seconds for which to keep
            the snapshot.
        :param access_type: For a file system or VMware NFS datastore snapshot
            schedule, indicates whether the snapshot created by the schedule
            has checkpoint or protocol type access. Value is
            FilesystemSnapAccessTypeEnum.
        :return: constructed embedded instance in a dict.
        """
        if not isinstance(days_of_month, list):
            raise ValueError(
                'days_of_month of UnitySnapScheduleRule every_month rule '
                'should be a list.')
        if not days_of_month:
            raise ValueError(
                'days_of_month of UnitySnapScheduleRule every_month rule '
                'cannot be empty list.')
        return UnitySnapScheduleRule.to_embedded(
            ScheduleTypeEnum.NTH_DAYOFMONTH_AT_HHMM,
            days_of_month=days_of_month,
            hours=[hour],
            minute=minute,
            is_auto_delete=is_auto_delete,
            retention_time=retention_time,
            access_type=access_type,
        )


class UnitySnapScheduleRuleList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySnapScheduleRule


class UnitySnapSchedule(UnityResource):
    @classmethod
    def create(cls, cli, name, rules,
               is_sync_replicated=None, skip_sync_to_remote_system=None):
        """
        :param cli:
        :param name: Name of new schedule.
        :param rules: Rules that apply to the snapshot schedule, as defined by
            the `UnitySnapScheduleRule` resource type. Each value is a
            `UnitySnapScheduleRule` instance.
        :param is_sync_replicated: Indicates that all operations on the
            snapshot schedule will be synchronously replicated to the peer
            system.
        :param skip_sync_to_remote_system: For internal system use only. Skip
            the invocation of the snapshot schedule creation method with the
            same parameters on the remote system. If the method is invoked by
            the user, this attribute is not required. The value should be true
            when the operation is executed from a remote system, to prevent
            from syncing it back to the original storage.
        :return: the created `UnitySnapSchedule` instance.
        """

        resp = cli.post(cls().resource_class,
                        name=name,
                        rules=rules,
                        isSyncReplicated=is_sync_replicated,
                        skipSyncToRemoteSystem=skip_sync_to_remote_system)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def modify(self, add_rules=None, remove_rule_ids=None,
               skip_sync_to_remote_system=None):
        """
        :param add_rules: Rules to add to the snapshot schedule, as defined by
            the UnitySnapScheduleRule instance. Pass the desired values for the
             additional rules instead of the unique identifiers of existing
             rules. Each value is a `UnitySnapScheduleRule` instance.
        :param remove_rule_ids: Unique identifiers of the rules to remove from
            the snapshot schedule.
        :param skip_sync_to_remote_system: For internal system use only. Skip
            the invocation of the snapshot schedule modification method with
            the same parameters on the remote system. If the method is invoked
            by the user, this attribute is not required. The value should be
            true when the operation is executed from a remote system, to
            prevent from syncing it back to the original storage.
        :return:
        """
        req_body = self._cli.make_body(
            addRules=add_rules, removeRuleIds=remove_rule_ids,
            skipSyncToRemoteSystem=skip_sync_to_remote_system)
        resp = self.action('modify', **req_body)
        resp.raise_if_err()
        return resp


class UnitySnapScheduleList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySnapSchedule
