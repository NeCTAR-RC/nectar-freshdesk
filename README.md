## Configuration

In the Freshdesk admin portal, go to Automations (under Helpdesk Productivity).

Add two rules, one for `Ticket Creation` and one for `Ticket Updates`.

### Ticket Creation

Rule name: *OpenStack information*
On tickets with these properties:
  - Match ANY of the below
    - In Tickets
    - If Description
    - Is not
    - '' (empty quotes)
Perform these actions:
  - Trigger webhook
  - Request type: *POST*
  - URL: `https://hostname/addinfo`
  - Requires authentication: enabled
  - I have an API key: ???
  - Encoding: JSON
  - Content: Advanced

Enter the following:

```json
{
    "action": "create",
    "ticket_id": {{ticket.id}},
    "source": "{{ticket.description}}",
    "email": "{{ticket.contact.email}}"
}
```


### Ticket Update

Rule name: *OpenStack information*
When an action performed by: *Agent or requester*
Involves any of these events:
  - Note is added: Public note
  - Reply is sent
On tickets with these properties:
  - None required here
Perform these actions:
  - Trigger webhook
  - Request type: *POST*
  - URL: `https://hostname/addinfo`
  - Requires authentication: enabled
  - I have an API key: ???
  - Encoding: JSON
  - Content: Advanced

Enter the following:

```json
{
    "action": "update",
    "ticket_id": {{ticket.id}},
    "source": "{{ticket.latest_public_comment}}",
    "email": "{{ticket.contact.email}}"
 }
```

## Testing

Create an application credential:

```
openstack application credential create --role Admin nectar-freshdesk
```

Create yourself with a `.env` file with your settings:

```
FLASK_APP=nectar_freshdesk/wsgi
FLASK_DEBUG=1
FLASK_RUN_PORT=8613
OS_DEFAULT__TRANSPORT_URL=rabbit://freshdesk:test@rabbit.example.com:5671/freshdesk
OS_FRESHDESK__DOMAIN=dhdnectartest.freshdesk.com
OS_FRESHDESK__API_KEY=<your api key>
OS_OSLO_MESSAGING_RABBIT__AMQP_DURABLE_QUEUES=True
OS_OSLO_MESSAGING_RABBIT__SSL=True
OS_SERVICE_AUTH__AUTH_URL=http://keystone.example.com:5000/v3/
OS_SERVICE_AUTH__AUTH_TYPE=v3applicationcredential
OS_SERVICE_AUTH__APPLICATION_CREDENTIAL_ID=<credential id>
OS_SERVICE_AUTH__APPLICATION_CREDENTIAL_SECRET=<credential secret>
```

Create yourself a freshdesk vhost on your Rabbit server:

```
rabbitmqctl add_vhost freshdesk
rabbitmqctl add_user freshdesk test
rabbitmqctl set_permissions -p freshdesk freshdesk '.*' '.*' '.*'
rabbitmqctl set_policy -p freshdesk max-length '.*' '{"max-length":100000}'
```

Ensure you have your virtualenv loaded
```
workon myvenv
```

Install the app into your venv
```
pip install -e .
```

Run the API:
```
flask run
```

Run the agent:
```
nectar-freshdesk-agent
```

Run the AI triage worker (optional, see below):
```
nectar-freshdesk-triage
```

Simulate a FD webhook call:
```
curl -X POST -H "Content-Type: application/json" --data '{"action": "create", "ticket_id": "603", "source": "ticket body 21d43012-7408-4426-8121-6b5351f63e9d", "email": "andy.botting@unimelb.edu.au"}' http://localhost:8613/addinfo
```

For best results use a real `ticket_id` and use a UUID of an instance in the `source` field.

## AI triage

When `[triage] enabled` is set, the API also queues each new ticket for the
triage worker (`nectar-freshdesk-triage`). The worker asks an AI agent on the
Nectar agents platform to investigate the ticket and adds the answer to the
ticket as a private note, tagged `ai-triaged`. It never replies to the
requester.

Only the ticket ID is sent to the agent, which reads the ticket itself with
its own read-only Freshdesk access. The agent is reached over the
[A2A protocol](https://a2a-protocol.org/) with a Keycloak client credentials
token. The triage worker has a queue of its own, so a slow or unavailable
agent never delays the OpenStack information notes.

Create a confidential client in Keycloak with only service accounts enabled
(no standard flow), and whatever audience mapper the agents platform route
requires. Then add to your settings:

```
OS_TRIAGE__ENABLED=True
OS_TRIAGE__AGENT_URL=https://agents.example.com/agents/<namespace>/<agent>
OS_TRIAGE__TOKEN_URL=https://sso.example.com/auth/realms/<realm>/protocol/openid-connect/token
OS_TRIAGE__CLIENT_ID=nectar-freshdesk
OS_TRIAGE__CLIENT_SECRET=<client secret>
```

`OS_TRIAGE__ENABLED` must be set for both the API and the triage worker.
Other options (`actions`, `timeout`, `poll_interval`, `http_timeout`,
`retries`, `scope`) are described in `nectar_freshdesk/config.py`.
