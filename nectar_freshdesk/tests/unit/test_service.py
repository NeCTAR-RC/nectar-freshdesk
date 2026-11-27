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

from nectar_freshdesk.tests.unit import base


class TestHealthcheck(base.TestCase):
    def test_healthcheck(self):
        response = self.client.get('/healthcheck')

        self.assertEqual(200, response.status_code)

    def test_other_paths_reach_the_application(self):
        # The healthcheck used to answer every request
        self.assertEqual(404, self.client.get('/nope').status_code)
        self.assertEqual(405, self.client.get('/addinfo').status_code)
