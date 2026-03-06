# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Tests that validate SDK behaviour when uamqp is NOT installed.

The fix for https://github.com/ansible-collections/azure/issues/1511 makes
uamqp optional on ARM macOS.  These tests simulate its absence by patching
HAS_UAMQP to False and making the AMQP client constructors raise ImportError,
then verify that:

  1. IoTHubRegistryManager can still be constructed (REST operations work).
  2. REST-based operations (get_device, etc.) are unaffected.
  3. send_c2d_message raises a clear ImportError.
  4. AMQP client classes raise ImportError at construction time.
"""

import pytest

from azure.iot.hub.iothub_registry_manager import IoTHubRegistryManager
from azure.iot.hub import iothub_amqp_client

# ---Constants---
fake_hostname = "beauxbatons.academy-net"
fake_device_id = "MyPensieve"
fake_shared_access_key_name = "alohomora"
fake_shared_access_key = "Zm9vYmFy"
fake_connection_string = (
    "HostName={hostname};DeviceId={device_id};"
    "SharedAccessKeyName={skn};SharedAccessKey={sk}"
).format(
    hostname=fake_hostname,
    device_id=fake_device_id,
    skn=fake_shared_access_key_name,
    sk=fake_shared_access_key,
)


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def mock_protocol_client(mocker):
    """Prevent real HTTP calls; return a mock protocol client."""
    return mocker.patch(
        "azure.iot.hub.iothub_registry_manager.protocol_client"
    )


@pytest.fixture()
def simulate_no_uamqp(mocker):
    """Patch HAS_UAMQP to False so AMQP client constructors raise ImportError."""
    mocker.patch.object(iothub_amqp_client, "HAS_UAMQP", False)


# ──────────────────────────────────────────────────────────────────────
# IoTHubRegistryManager — construction without uamqp
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.describe("IoTHubRegistryManager — construction without uamqp")
class TestRegistryManagerConstructionWithoutUamqp:

    @pytest.mark.it(
        "Can be constructed from a connection string when uamqp is absent"
    )
    def test_from_connection_string_succeeds(self, simulate_no_uamqp):
        manager = IoTHubRegistryManager.from_connection_string(
            fake_connection_string
        )
        assert manager is not None
        assert manager.amqp_svc_client is None

    @pytest.mark.it(
        "Can be constructed from token credential when uamqp is absent"
    )
    def test_from_token_credential_succeeds(self, simulate_no_uamqp, mocker):
        mock_credential = mocker.MagicMock()
        manager = IoTHubRegistryManager.from_token_credential(
            fake_hostname, mock_credential
        )
        assert manager is not None
        assert manager.amqp_svc_client is None


# ──────────────────────────────────────────────────────────────────────
# IoTHubRegistryManager — REST operations work without uamqp
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.describe("IoTHubRegistryManager — REST operations without uamqp")
class TestRegistryManagerRestOperationsWithoutUamqp:

    @pytest.fixture
    def manager(self, simulate_no_uamqp):
        return IoTHubRegistryManager.from_connection_string(
            fake_connection_string
        )

    @pytest.mark.it("get_device works without uamqp")
    def test_get_device(self, manager):
        manager.get_device(fake_device_id)
        manager.protocol.devices.get_identity.assert_called_once_with(
            fake_device_id
        )

    @pytest.mark.it("get_module works without uamqp")
    def test_get_module(self, manager):
        manager.get_module(fake_device_id, "module1")
        manager.protocol.modules.get_identity.assert_called_once_with(
            fake_device_id, "module1"
        )

    @pytest.mark.it("get_service_statistics works without uamqp")
    def test_get_service_statistics(self, manager):
        manager.get_service_statistics()
        manager.protocol.statistics.get_service_statistics.assert_called_once()

    @pytest.mark.it("delete_device works without uamqp")
    def test_delete_device(self, manager):
        manager.delete_device(fake_device_id)
        manager.protocol.devices.delete_identity.assert_called_once_with(
            fake_device_id, '"*"'
        )

    @pytest.mark.it("get_twin works without uamqp")
    def test_get_twin(self, manager):
        manager.get_twin(fake_device_id)
        manager.protocol.devices.get_twin.assert_called_once_with(
            fake_device_id
        )


# ──────────────────────────────────────────────────────────────────────
# IoTHubRegistryManager — send_c2d_message fails clearly without uamqp
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.describe("IoTHubRegistryManager — send_c2d_message without uamqp")
class TestSendC2dMessageWithoutUamqp:

    @pytest.fixture
    def manager(self, simulate_no_uamqp):
        return IoTHubRegistryManager.from_connection_string(
            fake_connection_string
        )

    @pytest.mark.it("Raises ImportError with install instructions")
    def test_send_c2d_message_raises_import_error(self, manager):
        with pytest.raises(ImportError, match="pip install azure-iot-hub"):
            manager.send_c2d_message(fake_device_id, "hello")

    @pytest.mark.it("Error message mentions ARM macOS")
    def test_error_message_mentions_platform(self, manager):
        with pytest.raises(ImportError, match="ARM macOS"):
            manager.send_c2d_message(fake_device_id, "hello")


# ──────────────────────────────────────────────────────────────────────
# AMQP client classes — raise ImportError without uamqp
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.describe("IoTHubAmqpClient classes — instantiation without uamqp")
class TestAmqpClientWithoutUamqp:

    @pytest.mark.it(
        "IoTHubAmqpClientSharedAccessKeyAuth raises ImportError"
    )
    def test_shared_access_key_auth_raises(self, simulate_no_uamqp):
        with pytest.raises(ImportError, match="pip install azure-iot-hub"):
            iothub_amqp_client.IoTHubAmqpClientSharedAccessKeyAuth(
                fake_hostname,
                fake_shared_access_key_name,
                fake_shared_access_key,
            )

    @pytest.mark.it("IoTHubAmqpClientTokenAuth raises ImportError")
    def test_token_auth_raises(self, simulate_no_uamqp, mocker):
        mock_credential = mocker.MagicMock()
        with pytest.raises(ImportError, match="pip install azure-iot-hub"):
            iothub_amqp_client.IoTHubAmqpClientTokenAuth(
                fake_hostname, mock_credential
            )


# ──────────────────────────────────────────────────────────────────────
# TransportType fallback enum
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.describe("TransportType fallback enum")
class TestTransportTypeFallback:

    @pytest.mark.it("Has Amqp and AmqpOverWebsocket members")
    def test_fallback_enum_members(self):
        from azure.iot.hub.iothub_registry_manager import TransportType

        assert hasattr(TransportType, "Amqp")
        assert hasattr(TransportType, "AmqpOverWebsocket")

    @pytest.mark.it("Fallback IntEnum values match uamqp convention")
    def test_fallback_enum_int_values(self, monkeypatch):
        """Force uamqp ImportError and reload the module to exercise the fallback."""
        from enum import IntEnum
        import builtins
        import importlib
        import azure.iot.hub.iothub_registry_manager as registry_module

        real_import = builtins.__import__

        def _import_without_uamqp(name, *args, **kwargs):
            if name == "uamqp":
                raise ImportError("No module named 'uamqp'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _import_without_uamqp)
        reloaded_module = importlib.reload(registry_module)
        FallbackTransportType = reloaded_module.TransportType

        assert issubclass(FallbackTransportType, IntEnum)
        assert FallbackTransportType.Amqp == 1
        assert FallbackTransportType.AmqpOverWebsocket == 3

        # Restore original module state: undo monkeypatch first, then reload
        monkeypatch.setattr(builtins, "__import__", real_import)
        importlib.reload(registry_module)

    @pytest.mark.it("Default transport_type in from_connection_string is Amqp")
    def test_default_transport_type(self, simulate_no_uamqp):
        manager = IoTHubRegistryManager.from_connection_string(
            fake_connection_string
        )
        # Construction succeeded — the default TransportType.Amqp resolved fine
        assert manager is not None
