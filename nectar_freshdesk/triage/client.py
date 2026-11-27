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

"""Client of the AI triage agent.

The agent is a kagent agent on the agents platform, reached over the A2A
protocol with a Keycloak client credentials token. The official A2A SDK is
asynchronous, so triage() runs one event loop per call for the threaded
oslo.messaging executor.
"""

import asyncio
import time

from a2a import client as a2a_client
from a2a import helpers
from a2a import types
from a2a.utils import constants
import httpx
from oslo_config import cfg
from oslo_log import log


CONF = cfg.CONF
LOG = log.getLogger(__name__)

# Seconds before expiry at which a token is replaced
TOKEN_LEEWAY = 30


class TriageError(Exception):
    """The agent did not produce a triage."""


class KeycloakAuth(httpx.Auth):
    """Adds a Keycloak client credentials token to each request."""

    requires_response_body = True

    def __init__(self, token_url, client_id, client_secret, scope=None):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self._token = None
        self._expires = 0

    def _token_request(self):
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        if self.scope:
            data['scope'] = self.scope
        return httpx.Request('POST', self.token_url, data=data)

    def _store(self, response):
        if response.status_code != 200:
            # The body may describe the client, never log or raise it
            raise TriageError(
                f'Keycloak token request failed: {response.status_code}'
            )
        token = response.json()
        self._token = token['access_token']
        self._expires = time.monotonic() + token.get('expires_in', 60)

    def auth_flow(self, request):
        if not self._token or time.monotonic() > self._expires - TOKEN_LEEWAY:
            self._store((yield self._token_request()))
        request.headers['Authorization'] = f'Bearer {self._token}'
        response = yield request
        if response.status_code == 401:
            # Token revoked or keys rotated, retry once with a new one
            self._store((yield self._token_request()))
            request.headers['Authorization'] = f'Bearer {self._token}'
            yield request


def _agent_card():
    # Built from configuration rather than fetched: the card the platform
    # serves advertises the agent's in-cluster address.
    return types.AgentCard(
        name='triage',
        supported_interfaces=[
            types.AgentInterface(
                url=CONF.triage.agent_url,
                protocol_binding='JSONRPC',
                protocol_version=constants.PROTOCOL_VERSION_1_0,
            )
        ],
    )


def _task_text(task):
    texts = [helpers.get_artifact_text(a) for a in task.artifacts]
    text = '\n\n'.join(t for t in texts if t)
    if not text and task.status.HasField('message'):
        text = helpers.get_message_text(task.status.message)
    return text


def _result(task):
    """Return the text of a finished task, None while it is running."""
    state = task.status.state
    if state == types.TaskState.TASK_STATE_COMPLETED:
        text = _task_text(task)
        if not text:
            raise TriageError(f'Task {task.id} completed with no output')
        return text
    if (
        state in constants.TERMINAL_TASK_STATES
        or state in constants.INTERRUPTED_TASK_STATES
    ):
        # Nobody is there to answer an agent that asks for input
        raise TriageError(
            f'Task {task.id} ended as {types.TaskState.Name(state)}'
        )
    return None


def _http_client():
    auth = KeycloakAuth(
        CONF.triage.token_url,
        CONF.triage.client_id,
        CONF.triage.client_secret,
        CONF.triage.scope,
    )
    return httpx.AsyncClient(auth=auth, timeout=CONF.triage.http_timeout)


async def _triage(prompt, message_id):
    async with _http_client() as http:
        # polling asks the agent to return as soon as the task exists. A
        # triage takes minutes, longer than the gateways keep an idle
        # connection open.
        config = a2a_client.ClientConfig(
            streaming=False, polling=True, httpx_client=http
        )
        client = await a2a_client.create_client(_agent_card(), config)
        request = types.SendMessageRequest(
            message=types.Message(
                message_id=message_id,
                role=types.Role.ROLE_USER,
                parts=[types.Part(text=prompt)],
            )
        )
        task = None
        async for response in client.send_message(request):
            if response.HasField('message'):
                return helpers.get_message_text(response.message)
            if response.HasField('task'):
                task = response.task
        if task is None:
            raise TriageError('Agent returned neither a task nor a message')

        LOG.info('Triage task %s started', task.id)
        deadline = time.monotonic() + CONF.triage.timeout
        while True:
            text = _result(task)
            if text is not None:
                return text
            if time.monotonic() > deadline:
                raise TriageError(
                    f'Task {task.id} not finished after '
                    f'{CONF.triage.timeout} seconds'
                )
            await asyncio.sleep(CONF.triage.poll_interval)
            task = await client.get_task(types.GetTaskRequest(id=task.id))


def triage(prompt, message_id):
    """Ask the agent and return its answer as text.

    message_id identifies the request to the agent. Sending the same one
    again continues the earlier run instead of starting a second, which
    makes a retry after a network error safe.
    """
    attempts = max(CONF.triage.retries, 1)
    for attempt in range(1, attempts + 1):
        try:
            return asyncio.run(_triage(prompt, message_id))
        except (httpx.TransportError, a2a_client.A2AClientError) as e:
            if attempt == attempts:
                raise
            LOG.warning('Triage attempt %s failed, retrying: %s', attempt, e)
            time.sleep(min(2**attempt, 30))
