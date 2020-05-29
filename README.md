

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


### Testing

curl -X POST -H "Content-Type: application/json" -d '{"action": "update", "ticket_id": "574", "source": "What about the instance 64cc9d74-230a-4df6-a435-d79628c78dc5 or how about the IP address 115.146.82.195 maybe", "email": "andrew.botting@unimelb.edu.au"}' https://hostname/openstack/addinfo
