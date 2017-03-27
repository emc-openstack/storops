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

from storops.unity.resource import UnityResource
from storops.exception import UnityResourceNotFoundError, \
    UnityResourceNotSupportedError


__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class UnityType(UnityResource):
    resource_class = 'type'

    _fields = ('name', 'description', 'documentation', 'type',
               'attributes.name', 'attributes.initialValue', 'attributes.type',
               'attributes.description', 'attributes.displayValue')

    def _get_raw_resource(self):
        url = '/api/types/{}'.format(self._id)
        resp = self._cli.rest_get(url, fields=self._fields)
        try:
            # The only known exception is UnityResourceNotFoundError
            resp.raise_if_err()
        except UnityResourceNotFoundError:
            # We translate the type not found error as not supported error
            log.info('Resouce type [{}] is not supported.'.format(self._id))
            raise UnityResourceNotSupportedError("Resource is not supported.")
        return resp

    @property
    def fields(self):
        if self._id == 'type':
            ret = self._fields
        else:
            ret = tuple(sorted(att['name'] for att in self.attributes))
        return ret

    @property
    def fields_str(self):
        return ','.join(self.fields)
