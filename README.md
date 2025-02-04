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
  - URL: `https://hostnameaddinfo`
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

Simulate a FD webhook call:
```
curl -X POST -H "Content-Type: application/json" --data '{"action": "create", "ticket_id": "603", "source": "ticket body 21d43012-7408-4426-8121-6b5351f63e9d", "email": "andy.botting@unimelb.edu.au"}' http://localhost:8613/addinfo
```

For best results use a real `ticket_id` and use a UUID of an instance in the `source` field.
