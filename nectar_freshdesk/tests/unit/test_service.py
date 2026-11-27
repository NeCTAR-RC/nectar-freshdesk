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

from oslo_config import cfg

from nectar_freshdesk.tests.unit import base


CONF = cfg.CONF

INFO = {
    'action': 'create',
    'ticket_id': 1234,
    'email': 'my@user.com',
    'source': 'This is my ticket source',
}


class TestHealthcheck(base.TestCase):
    def test_healthcheck(self):
        response = self.client.get('/healthcheck')

        self.assertEqual(200, response.status_code)

    def test_other_paths_reach_the_application(self):
        # The healthcheck used to answer every request
        self.assertEqual(404, self.client.get('/nope').status_code)
        self.assertEqual(405, self.client.get('/addinfo').status_code)


@mock.patch('nectar_freshdesk.openstack.messaging.get_rpc_client')
class TestAddInfo(base.TestCase):
    def test_missing_fields(self, mock_get_client):
        response = self.client.post('/addinfo', json={'action': 'create'})

        self.assertEqual(422, response.status_code)
        mock_get_client.assert_not_called()

    def test_addinfo_triage_disabled(self, mock_get_client):
        response = self.client.post('/addinfo', json=INFO)

        self.assertEqual(200, response.status_code)
        mock_get_client.assert_called_once_with()
        mock_get_client.return_value.cast.assert_called_once_with(
            mock.ANY, 'info', info=INFO
        )

    def test_addinfo_triage_enabled(self, mock_get_client):
        CONF.set_override('enabled', True, group='triage')

        response = self.client.post('/addinfo', json=INFO)

        self.assertEqual(200, response.status_code)
        (triage_target,), _ = mock_get_client.call_args
        self.assertEqual('nectar-freshdesk-triage', triage_target.topic)
        self.assertEqual(
            [
                mock.call(mock.ANY, 'info', info=INFO),
                mock.call(mock.ANY, 'triage', info=INFO),
            ],
            mock_get_client.return_value.cast.call_args_list,
        )

    def test_addinfo_triage_other_action(self, mock_get_client):
        CONF.set_override('enabled', True, group='triage')
        info = dict(INFO, action='update')

        response = self.client.post('/addinfo', json=info)

        self.assertEqual(200, response.status_code)
        mock_get_client.return_value.cast.assert_called_once_with(
            mock.ANY, 'info', info=info
        )
