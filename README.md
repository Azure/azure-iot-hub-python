# Azure IoTHub Service SDK

The Azure IoTHub Service SDK for Python provides functionality for communicating with the Azure IoT Hub.

## Features

The SDK provides the following clients:

* ### IoT Hub Registry Manager

  * CRUD operations for devices and modules on IoT Hub
  * Get service and device registry statistics
  * Query device twins using a SQL-like language
  * Retrieve and update device twins and module twins
  * Invoke direct methods on devices and modules
  * **Cloud-to-Device (C2D) messaging** over AMQP (requires `uamqp` — see [Installation](#installation) below)
  * Bulk create, update, or delete device identities

* ### IoT Hub Configuration Manager

  * CRUD operations for IoT Hub configurations

* ### IoT Hub Job Manager

  * Schedule and manage jobs for twin updates and direct method invocations
  * Import and export device identities in bulk

* ### IoT Hub HTTP Runtime Manager

  * Receive and complete/reject/abandon Cloud-to-Device messages from the device feedback queue

* ### Digital Twin Client

  * Get and update digital twins
  * Invoke commands on digital twin components

## Installation

### Standard installation

```bash
pip install azure-iot-hub
```

This installs all dependencies needed for every feature **except** Cloud-to-Device (C2D) AMQP messaging on ARM macOS / Apple Silicon (see below).

### Cloud-to-Device (C2D) messaging and `uamqp`

The `send_c2d_message` method on `IoTHubRegistryManager` uses the [uamqp](https://pypi.org/project/uamqp/) library, which is a C extension that must be compiled from source.

| Platform | C2D messaging support | Notes |
|---|---|---|
| Windows | Included automatically | `uamqp` is installed as part of `pip install azure-iot-hub` |
| Linux | Included automatically | `uamqp` is installed as part of `pip install azure-iot-hub` |
| macOS (Intel) | Included automatically | `uamqp` is installed as part of `pip install azure-iot-hub` |
| macOS (Apple Silicon / ARM) | **Not installed automatically** | Recent versions of Xcode/clang enforce stricter C type checking that breaks the `uamqp` build. See below. |

#### Apple Silicon macOS: opting in to C2D messaging

If your Xcode and clang version are compatible, you can install `uamqp` explicitly using the `uamqp` extra:

```bash
pip install azure-iot-hub[uamqp]
```

If `uamqp` cannot be built in your environment, all other SDK features (device/module CRUD, twin operations, direct methods, digital twins, jobs, etc.) work without it. Calling `send_c2d_message` without `uamqp` installed raises an `ImportError` with instructions.

#### AMQP transport options

When `uamqp` is available, C2D messaging supports two transport modes, controlled by the `transport_type` parameter:

```python
from uamqp import TransportType

# Default: AMQP over TCP (port 5671)
registry_manager = IoTHubRegistryManager.from_connection_string(connection_string)

# AMQP over WebSocket (port 443) — useful when port 5671 is blocked by a firewall
registry_manager = IoTHubRegistryManager.from_connection_string(
    connection_string,
    transport_type=TransportType.AmqpOverWebsocket
)
```

## IoTHub Samples

Check out the [samples repository](https://github.com/Azure/azure-iot-hub-python/tree/main/samples) for more detailed samples.

Notable C2D samples:

- [`iothub_registry_manager_c2d_sample.py`](https://github.com/Azure/azure-iot-hub-python/tree/main/samples/iothub_registry_manager_c2d_sample.py) — basic C2D messaging
- [`iothub_registry_manager_c2d_amqp_over_websocket_sample.py`](https://github.com/Azure/azure-iot-hub-python/tree/main/samples/iothub_registry_manager_c2d_amqp_over_websocket_sample.py) — C2D over WebSocket

## Getting help and finding API docs

API documentation for this package is available via [Microsoft Docs](https://docs.microsoft.com/python/api/azure-iot-hub/azure.iot.hub?view=azure-python)

Additionally, the SDK makes use of docstrings which means you can find API documentation directly through Python with use of the [help](https://docs.python.org/3/library/functions.html#help) command:

```python
>>> from azure.iot.hub import IoTHubRegistryManager
>>> help(IoTHubRegistryManager)
```
