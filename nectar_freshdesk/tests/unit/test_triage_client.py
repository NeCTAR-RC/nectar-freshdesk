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

import json
from unittest import mock

from a2a import client as a2a_client
from a2a import types
from google.protobuf import json_format
import httpx
from oslo_config import cfg

from nectar_freshdesk.tests.unit import base
from nectar_freshdesk.triage import client


CONF = cfg.CONF

WORKING = types.TaskState.TASK_STATE_WORKING
COMPLETED = types.TaskState.TASK_STATE_COMPLETED
FAILED = types.TaskState.TASK_STATE_FAILED
INPUT_REQUIRED = types.TaskState.TASK_STATE_INPUT_REQUIRED


def fake_task(state, text=None, status_text=None):
    task = types.Task(id='task-1', context_id='ctx-1')
    task.status.state = state
    if text:
        task.artifacts.add(artifact_id='a1', parts=[types.Part(text=text)])
    if status_text:
        task.status.message.CopyFrom(
            types.Message(
                message_id='m1',
                role=types.Role.ROLE_AGENT,
                parts=[types.Part(text=status_text)],
            )
        )
    return task


class FakePlatform:
    """Keycloak and the agent's A2A endpoint behind one httpx transport."""

    def __init__(self, send_result, tasks=()):
        self.send_result = send_result
        self.tasks = list(tasks)
        self.token_requests = []
        self.rpc_requests = []
        self.token_status = 200
        self.reject_tokens = set()
        self.fail_rpc = 0

    def handler(self, request):
        if request.url.host == 'sso.example.com':
            self.token_requests.append(request)
            if self.token_status != 200:
                return httpx.Response(
                    self.token_status, json={'error': 'client-detail'}
                )
            token = f'token-{len(self.token_requests)}'
            return httpx.Response(
                200, json={'access_token': token, 'expires_in': 300}
            )

        token = request.headers['Authorization'].removeprefix('Bearer ')
        if token in self.reject_tokens:
            return httpx.Response(401)
        if self.fail_rpc:
            self.fail_rpc -= 1
            raise httpx.ConnectError('gateway down')

        self.rpc_requests.append(request)
        body = json.loads(request.content)
        if body['method'] == 'SendMessage':
            result = self.send_result
        else:
            result = self.tasks.pop(0)
        return httpx.Response(
            200,
            json={
                'jsonrpc': '2.0',
                'id': body['id'],
                'result': json_format.MessageToDict(result),
            },
        )

    def http_client(self):
        auth = client.KeycloakAuth(
            CONF.triage.token_url,
            CONF.triage.client_id,
            CONF.triage.client_secret,
            CONF.triage.scope,
        )
        return httpx.AsyncClient(
            auth=auth, transport=httpx.MockTransport(self.handler)
        )


class TestTriageClient(base.TestCase):
    def setUp(self):
        super().setUp()
        sleep = mock.patch('time.sleep')
        sleep.start()

    def assert_triage_error(self, platform):
        with self.assertRaises(client.TriageError) as cm:
            self.run_triage(platform)
        return cm.exception

    def run_triage(self, platform):
        with mock.patch.object(
            client, '_http_client', side_effect=platform.http_client
        ):
            return client.triage('Triage ticket 1234.', 'msg-1234')

    def test_triage_polls_until_completed(self):
        platform = FakePlatform(
            types.SendMessageResponse(task=fake_task(WORKING)),
            [fake_task(WORKING), fake_task(COMPLETED, text='All good')],
        )

        self.assertEqual('All good', self.run_triage(platform))

        send, get1, get2 = platform.rpc_requests
        self.assertEqual(
            'https://agents.example.com/agents/nectar-freshdesk/ticket-triage',
            str(send.url),
        )
        self.assertEqual('1.0', send.headers['A2A-Version'])
        self.assertEqual('Bearer token-1', send.headers['Authorization'])
        params = json.loads(send.content)['params']
        self.assertEqual('msg-1234', params['message']['messageId'])
        self.assertEqual('ROLE_USER', params['message']['role'])
        self.assertEqual(
            [{'text': 'Triage ticket 1234.'}], params['message']['parts']
        )
        # The agent must not hold the request open while it works
        self.assertTrue(params['configuration']['returnImmediately'])
        self.assertEqual('GetTask', json.loads(get2.content)['method'])
        self.assertEqual('task-1', json.loads(get2.content)['params']['id'])
        # One token serves the whole run
        self.assertEqual(1, len(platform.token_requests))

    def test_token_request(self):
        CONF.set_override('scope', 'agents', group='triage')
        platform = FakePlatform(
            types.SendMessageResponse(task=fake_task(COMPLETED, text='ok'))
        )

        self.run_triage(platform)

        form = dict(httpx.QueryParams(platform.token_requests[0].content))
        self.assertEqual(
            {
                'grant_type': 'client_credentials',
                'client_id': 'nectar-freshdesk',
                'client_secret': 'testsecret',
                'scope': 'agents',
            },
            form,
        )

    def test_token_refreshed_on_401(self):
        platform = FakePlatform(
            types.SendMessageResponse(task=fake_task(COMPLETED, text='ok'))
        )
        platform.reject_tokens = {'token-1'}

        self.assertEqual('ok', self.run_triage(platform))
        self.assertEqual(2, len(platform.token_requests))
        self.assertEqual(
            'Bearer token-2', platform.rpc_requests[0].headers['Authorization']
        )

    def test_token_failure_does_not_leak_response(self):
        platform = FakePlatform(None)
        platform.token_status = 401

        e = self.assert_triage_error(platform)
        self.assertNotIn('client-detail', str(e))
        self.assertEqual([], platform.rpc_requests)

    def test_message_response(self):
        message = types.Message(
            message_id='m1',
            role=types.Role.ROLE_AGENT,
            parts=[types.Part(text='Direct answer')],
        )
        platform = FakePlatform(types.SendMessageResponse(message=message))

        self.assertEqual('Direct answer', self.run_triage(platform))

    def test_completed_with_status_message_only(self):
        platform = FakePlatform(
            types.SendMessageResponse(
                task=fake_task(COMPLETED, status_text='From status')
            )
        )

        self.assertEqual('From status', self.run_triage(platform))

    def test_completed_without_output(self):
        platform = FakePlatform(
            types.SendMessageResponse(task=fake_task(COMPLETED))
        )

        self.assert_triage_error(platform)

    def test_failed_task(self):
        platform = FakePlatform(
            types.SendMessageResponse(task=fake_task(WORKING)),
            [fake_task(FAILED)],
        )

        e = self.assert_triage_error(platform)
        self.assertIn('TASK_STATE_FAILED', str(e))

    def test_input_required_is_an_error(self):
        platform = FakePlatform(
            types.SendMessageResponse(task=fake_task(INPUT_REQUIRED))
        )

        self.assert_triage_error(platform)

    def test_timeout(self):
        CONF.set_override('timeout', -1, group='triage')
        platform = FakePlatform(
            types.SendMessageResponse(task=fake_task(WORKING))
        )

        e = self.assert_triage_error(platform)
        self.assertIn('not finished', str(e))

    def test_retry_after_transport_error(self):
        platform = FakePlatform(
            types.SendMessageResponse(task=fake_task(COMPLETED, text='ok'))
        )
        platform.fail_rpc = 1

        self.assertEqual('ok', self.run_triage(platform))
        # The retry repeats the message ID so the agent does not run twice
        params = json.loads(platform.rpc_requests[0].content)['params']
        self.assertEqual('msg-1234', params['message']['messageId'])

    def test_retries_exhausted(self):
        platform = FakePlatform(None)
        platform.fail_rpc = 5

        self.assertRaises(
            (httpx.TransportError, a2a_client.A2AClientError),
            self.run_triage,
            platform,
        )
        self.assertEqual([], platform.rpc_requests)
        self.assertEqual(3, platform.fail_rpc)
