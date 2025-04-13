## Coding Conventions

- Always use **4 spaces** for indentation.
- Always use **double quotes** for strings.
- Never use `print()` for logging. Always use the client's logging methods.

## Initialization

All code must use the **OpenIAP Python client library**. Start by creating and connecting the client:

```python
from openiap import Client

client = Client()
client.connect()
client.signin(username="user", password="pass")
```

## Connection Lifecycle

If you're writing code that needs to reinitialize state when reconnecting (e.g., registering a queue or setting up a watch), implement an `on_connected()` function and hook it into the `on_client_event()` handler:

```python
def on_connected():
    client.register_queue("myqueue", handle_message)

def handle_event(event, count):
    if event["event"] == "SignedIn":
        on_connected()

client.on_client_event(handle_event)
```

## API Reference

Use the following methods when interacting with the OpenIAP platform:

### Database Operations

```python
client.query(collectionname, query, projection="", orderby="", skip=0, top=100, queryas="", explain=False)
client.aggregate(collectionname, aggregates="[]", queryas="", hint="", explain=False)
client.count(collectionname, query="", queryas="", explain=False)
client.distinct(collectionname, field, query="", queryas="", explain=False)
client.insert_one(collectionname, item, w=1, j=False)
client.insert_many(collectionname, items, w=1, j=False, skipresults=False)
client.update_one(collectionname, item, w=1, j=False)
client.insert_or_update_one(collectionname, item, uniqeness="_id", w=1, j=False)
client.delete_one(collectionname, id, recursive=False)
client.delete_many(collectionname, query="", recursive=False, ids=[])
```

### Collection & Index Management

```python
client.list_collections(includehist=False)
client.create_collection(collectionname, collation=None, timeseries=None, expire_after_seconds=0, change_stream_pre_and_post_images=False, capped=False, max=0, size=0)
client.drop_collection(collectionname)
client.get_indexes(collectionname)
client.create_index(collectionname, index, options="", name="")
client.drop_index(collectionname, indexname)
```

### Authentication

```python
client.connect()
client.signin(username="", password="")
client.disconnect()
```

### File Transfer

```python
client.upload(filepath, filename, mimetype="", metadata="", collectionname="")
client.download(collectionname, id, folder=".", filename="")
```

### Work Items

Work item queues contain a list of "units of work", something that needs to be processed. Items start in state `"new"`, and when you pop an item, the server updates its state to `"processing"`. Therefore it's **VITAL** that you always update the item's state to either `"retry"` (on error) or `"successful"` (on success) using `update_workitem`.

```python
client.push_workitem(wiq, wiqid, name, payload="{}", nextrun=0, success_wiqid="", failed_wiqid="", success_wiq="", failed_wiq="", priority=2, files=[])
client.pop_workitem(wiq, wiqid="", downloadfolder=".")
client.update_workitem(workitem, files=[])
client.delete_workitem(id)
```

### Events & Messaging

```python
# Register a change stream and call the callback every time an object is inserted, updated or deleted
client.watch(collectionname, paths, callback)  # callback(event, event_counter)
client.unwatch(watchid)

# Register a queue and handle incoming messages
client.register_queue(queuename, callback)  # callback(event, event_counter)

# Register an exchange and handle routed messages
client.register_exchange(exchangename, algorithm, routingkey="", addqueue=True, callback)

# Unregister a previously registered queue
client.unregister_queue(queuename)

# Send a message to a queue or exchange
client.queue_message(data, queuename="", exchangename="", routingkey="", replyto="", correlation_id="", striptoken=False, expiration=0)

# Send a message and wait for a response
client.rpc_async(data, queuename="", exchangename="", routingkey="", replyto="", correlation_id="", striptoken=False, expiration=0)
```

### Helpers

```python
client.enable_tracing("openiap=info")  # Optional: openiap=trace, openiap=debug, openiap=warn, openiap=error
client.disable_tracing()

client.set_f64_observable_gauge(name, value, description)
client.set_u64_observable_gauge(name, value, description)
client.set_i64_observable_gauge(name, value, description)
client.disable_observable_gauge(name)

client.info(...)      # Use instead of print() for normal logs
client.warn(...)      # Use for warnings
client.error(...)     # Use for error messages
client.verbose(...)   # Use for verbose output
client.trace(...)     # Use for deep tracing (e.g., callbacks, retries)

# This is automatically called by the library when converting Python objects
# Use manually only for debugging JSON parsing issues
client.stringify(obj)
```

---

## Logging

**Never use** `print()` or `logging`.

Use the OpenIAP logging methods instead:

- `client.info(...)`
- `client.warn(...)`
- `client.error(...)`
- `client.verbose(...)`
- `client.trace(...)`

---

## Example Pattern

Here is how to receive messages from a queue and handle work items:

```python
def handle_message(event, count):
    workitem = client.pop_workitem("q2")
    client.info("Processing workitem:", workitem["id"])
    # process work...
    workitem["state"] = "successful"
    client.update_workitem(workitem)

def on_connected():
    client.register_queue("q2", handle_message)

client = Client()
client.connect()
client.signin(username="admin", password="password")
client.on_client_event(lambda event, count: on_connected() if event["event"] == "SignedIn" else None)
```

