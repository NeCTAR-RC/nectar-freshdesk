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

from unittest import mock

import flask_testing
from oslo_config import cfg

from nectar_freshdesk import app


class TestCase(flask_testing.TestCase):
    def create_app(self):
        return app.create_app(
            conf_file='nectar_freshdesk/tests/etc/nectar-freshdesk.conf'
        )

    def setUp(self):
        super().setUp()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        super().tearDown()
        cfg.CONF.reset()
