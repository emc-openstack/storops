# coding=utf-8
# Copyright (c) 2017 Dell Inc. or its subsidiaries.
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

import operator


class UnityModel:
    def __init__(self, model):
        self.model = model.split(' ')[-1]
        self.series = self.model[0]

        if self.model.endswith('F'):
            self.is_all_flash = True
            self.model_base = self.model.rstrip('F')
        else:
            self.is_all_flash = False
            self.model_base = self.model

    def is_same_series(self, other):
        return (self.series == other.series) and (
                self.is_all_flash == other.is_all_flash)

    def compare(self, other, op):
        if not self.is_same_series(other):
            return False
        return op(int(self.model_base), int(other.model_base))

    def __eq__(self, other):
        return self.compare(other, operator.eq)

    def __gt__(self, other):
        return self.compare(other, operator.gt)

    def __ge__(self, other):
        return self.compare(other, operator.ge)

    def __lt__(self, other):
        return self.compare(other, operator.lt)

    def __le__(self, other):
        return self.compare(other, operator.le)
