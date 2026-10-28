# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import base64
import hashlib
import pytest
import hmac
from azure.core.credentials import AccessToken
from azure.iot.hub._pyamqp.constants import ManagementExecuteOperationResult, Role, TransportType
from azure.iot.hub._pyamqp.error import AMQPException, ErrorCondition
from azure.iot.hub._pyamqp.management_link import ManagementLink, PendingManagementOperation
from azure.iot.hub._pyamqp.message import Message, Properties
from azure.iot.hub._pyamqp.outcomes import Accepted
from azure.iot.hub._pyamqp.performatives import TransferFrame
from azure.iot.hub._pyamqp.receiver import ReceiverLink
from azure.iot.hub.iothub_amqp_client import (
    C2DMessageSendError,
    IoTHubAmqpClientSharedAccessKeyAuth,
    IoTHubAmqpClientTokenAuth,
)

"""---Constants---"""
fake_device_id = "device_id"
fake_message = "fake_message"
fake_app_prop = {"fake_prop1": "fake_value1"}
fake_sys_prop = {
    "contentType": "value1",
    "contentEncoding": "value2",
    "correlationId": "value3",
    "expiryTimeUtc": 1584727659,
    "messageId": 42,
}
fake_hostname = "hostname.mytest.net"
fake_shared_access_key_name = "test_key_name"
fake_shared_access_key = "Zm9vYmFy"
fake_token_scope = "https://token.net/.default"
fake_token = "fasdjkhg"
fake_token_expiry = 1584727659

expected_target = "amqps://" + fake_hostname + "/messages/devicebound"
expected_devicebound_to = "/devices/" + fake_device_id + "/messages/devicebound"


@pytest.fixture(autouse=True)
def mock_SendClient(mocker):
    return mocker.patch("azure.iot.hub.iothub_amqp_client.SendClient")


class SharedIotHubAmqpClientSendMessageToDeviceTests(object):
    @pytest.mark.it("Sends messages with application properties using the pyamqp SendClient")
    def test_send_message_to_device_app_prop(self, client, mocker, mock_SendClient):
        client.send_message_to_device(fake_device_id, fake_message, fake_app_prop)
        amqp_client_obj = mock_SendClient.return_value

        assert amqp_client_obj.send_message.call_count == 1
        msg_obj = amqp_client_obj.send_message.call_args[0][0]

        assert msg_obj.data == [fake_message.encode("utf-8")]
        assert msg_obj.properties.to == expected_devicebound_to
        assert msg_obj.application_properties == fake_app_prop

    @pytest.mark.it("Sends messages with system properties using the pyamqp SendClient")
    def test_send_message_to_device_sys_prop(self, client, mocker, mock_SendClient):
        client.send_message_to_device(fake_device_id, fake_message, fake_sys_prop)
        amqp_client_obj = mock_SendClient.return_value

        assert amqp_client_obj.send_message.call_count == 1
        msg_obj = amqp_client_obj.send_message.call_args[0][0]

        assert msg_obj.data == [fake_message.encode("utf-8")]
        assert msg_obj.properties.to == expected_devicebound_to
        assert msg_obj.application_properties == {}
        assert msg_obj.properties.content_type == fake_sys_prop["contentType"]
        assert msg_obj.properties.content_encoding == fake_sys_prop["contentEncoding"]
        assert msg_obj.properties.correlation_id == fake_sys_prop["correlationId"]
        assert msg_obj.properties.absolute_expiry_time == fake_sys_prop["expiryTimeUtc"]
        assert msg_obj.properties.message_id == fake_sys_prop["messageId"]

    @pytest.mark.it("Raises a C2DMessageSendError if pyamqp send_message raises an AMQPException")
    def test_raise_exception_on_send_fail(self, client, mocker, mock_SendClient):
        amqp_client_obj = mock_SendClient.return_value
        amqp_client_obj.send_message.side_effect = AMQPException(
            condition=ErrorCondition.UnknownError, description="fake failure"
        )
        with pytest.raises(C2DMessageSendError, match="C2D message send failure"):
            client.send_message_to_device(fake_device_id, fake_message, fake_app_prop)


class SharedIotHubAmqpClientDisconnectSyncTests(object):
    @pytest.mark.it(
        "Calls close() on the pyamqp SendClient and removes it when disconnect_sync() is called"
    )
    def test_disconnect_sync(self, client, mock_SendClient):
        assert client.amqp_client is not None
        amqp_client_obj = mock_SendClient.return_value

        client.disconnect_sync()

        assert amqp_client_obj.close.call_count == 1
        assert client.amqp_client is None


#############################################
# IoTHubAmqpClientSharedAccessKeyAuth Tests #
#############################################


class IoTHubAmqpClientSharedAccessKeyAuthTestConfig(object):
    @pytest.fixture
    def client(self):
        return IoTHubAmqpClientSharedAccessKeyAuth(
            hostname=fake_hostname,
            shared_access_key_name=fake_shared_access_key_name,
            shared_access_key=fake_shared_access_key,
        )


@pytest.mark.describe("IoTHubAmqpClientSharedAccessKeyAuth - Instantiation")
class TestIoTHubAmqpClientSharedAccessKeyAuthInstantiation(
    IoTHubAmqpClientSharedAccessKeyAuthTestConfig
):
    @pytest.mark.it(
        "Creates a JWTTokenAuth instance with the correct parameters and uses it to create an AMQP SendClient"
    )
    def test_create_JWTTokenAuth_with_sas_token(self, mocker, mock_SendClient):
        amqp_token_init_mock = mocker.patch("azure.iot.hub.iothub_amqp_client.JWTTokenAuth")
        amqp_token_mock = amqp_token_init_mock.return_value

        IoTHubAmqpClientSharedAccessKeyAuth(
            fake_hostname, fake_shared_access_key_name, fake_shared_access_key
        )

        # JWTTokenAuth creation
        assert amqp_token_init_mock.call_count == 1
        _, kwargs = amqp_token_init_mock.call_args
        assert kwargs["uri"] == "https://" + fake_hostname
        assert kwargs["audience"] == "https://" + fake_hostname
        assert callable(kwargs["get_token"])
        assert kwargs["token_type"] == b"servicebus.windows.net:sastoken"

        # AMQP SendClient is created
        assert mock_SendClient.call_count == 1
        assert mock_SendClient.call_args == mocker.call(
            hostname=fake_hostname,
            target=expected_target,
            auth=amqp_token_mock,
            keep_alive_interval=120,
            transport_type=TransportType.Amqp,
        )

    @pytest.mark.it(
        "Creates a JWTTokenAuth instance with the correct parameters and uses it to create an AMQP over Websocket SendClient"
    )
    def test_create_JWTTokenAuth_with_sas_token_amqp_over_websocket(self, mocker, mock_SendClient):
        amqp_token_init_mock = mocker.patch("azure.iot.hub.iothub_amqp_client.JWTTokenAuth")
        amqp_token_mock = amqp_token_init_mock.return_value

        IoTHubAmqpClientSharedAccessKeyAuth(
            fake_hostname,
            fake_shared_access_key_name,
            fake_shared_access_key,
            transport_type=TransportType.AmqpOverWebsocket,
        )

        # JWTTokenAuth creation
        assert amqp_token_init_mock.call_count == 1
        _, kwargs = amqp_token_init_mock.call_args
        assert kwargs["uri"] == "https://" + fake_hostname
        assert kwargs["audience"] == "https://" + fake_hostname
        assert callable(kwargs["get_token"])
        assert kwargs["token_type"] == b"servicebus.windows.net:sastoken"

        # AMQP over Websocket SendClient is created
        assert mock_SendClient.call_count == 1
        assert mock_SendClient.call_args == mocker.call(
            hostname=fake_hostname,
            target=expected_target,
            auth=amqp_token_mock,
            keep_alive_interval=120,
            transport_type=TransportType.AmqpOverWebsocket,
        )

    @pytest.mark.it(
        "Signs the SAS token with HMAC-SHA256 when the JWTTokenAuth get_token callback is invoked"
    )
    def test_get_token_callback_signs_sas_with_hmac(self, mocker):
        hmac_mock = mocker.patch.object(hmac, "HMAC")
        hmac_digest_mock = hmac_mock.return_value.digest
        hmac_digest_mock.return_value = b"\xd2\x06\xf7\x12\xf1\xe9\x95$\x90\xfd\x12\x9a\xb1\xbe\xb4\xf8\xf3\xc4\x1ap\x8a\xab'\x8a.D\xfb\x84\x96\xca\xf3z"

        amqp_token_init_mock = mocker.patch("azure.iot.hub.iothub_amqp_client.JWTTokenAuth")

        IoTHubAmqpClientSharedAccessKeyAuth(
            fake_hostname, fake_shared_access_key_name, fake_shared_access_key
        )

        # pyamqp's JWTTokenAuth resolves tokens lazily via the get_token callback rather
        # than at construction, so invoke the captured callback to drive the SAS-signing path.
        get_token = amqp_token_init_mock.call_args.kwargs["get_token"]
        get_token()

        assert hmac_mock.call_count == 1
        assert hmac_mock.call_args == mocker.call(
            base64.b64decode(fake_shared_access_key + "="), mocker.ANY, hashlib.sha256
        )
        assert hmac_digest_mock.call_count == 1


@pytest.mark.describe("IoTHubAmqpClientSharedAccessKeyAuth - .send_message_to_device()")
class TestIoTHubAmqpClientSharedAccessKeyAuthSendMessageToDevice(
    IoTHubAmqpClientSharedAccessKeyAuthTestConfig, SharedIotHubAmqpClientSendMessageToDeviceTests
):
    pass


@pytest.mark.describe("IoTHubAmqpClientSharedAccessKeyAuth - .disconnect_sync()")
class TestIoTHubAmqpClientSharedAccessKeyAuthDisconnectSync(
    IoTHubAmqpClientSharedAccessKeyAuthTestConfig, SharedIotHubAmqpClientDisconnectSyncTests
):
    pass


###################################
# IoTHubAmqpClientTokenAuth Tests #
###################################


class IoTHubAmqpClientTokenAuthTestConfig(object):
    @pytest.fixture
    def mock_azure_identity_TokenCredential(self, mocker):
        mock = mocker.MagicMock()
        mock.get_token.return_value = AccessToken(fake_token, fake_token_expiry)
        return mock

    @pytest.fixture
    def client(self, mock_azure_identity_TokenCredential):
        return IoTHubAmqpClientTokenAuth(
            hostname=fake_hostname,
            token_credential=mock_azure_identity_TokenCredential,
            token_scope=fake_token_scope,
        )


@pytest.mark.describe("IoTHubAmqpClientTokenAuth - Instantiation")
class TestIotHubAmqpClientTokenAuthInstantiation(IoTHubAmqpClientTokenAuthTestConfig):
    @pytest.mark.it(
        "Creates a JWTTokenAuth instance with the correct parameters and uses it to create an AMQP SendClient when a token scope is specified"
    )
    def test_create_JWTTokenAuth_with_bearer_token_custom_scope(
        self, mocker, mock_azure_identity_TokenCredential, mock_SendClient
    ):
        amqp_token_init_mock = mocker.patch("azure.iot.hub.iothub_amqp_client.JWTTokenAuth")
        amqp_token_mock = amqp_token_init_mock.return_value

        IoTHubAmqpClientTokenAuth(
            fake_hostname, mock_azure_identity_TokenCredential, token_scope=fake_token_scope
        )

        # JWTTokenAuth Creation
        assert amqp_token_init_mock.call_count == 1
        _, kwargs = amqp_token_init_mock.call_args
        assert kwargs["uri"] == "https://" + fake_hostname
        assert kwargs["audience"] == fake_token_scope
        assert callable(kwargs["get_token"])
        assert kwargs["token_type"] == b"bearer"

        # AMQP SendClient is created
        assert mock_SendClient.call_count == 1
        assert mock_SendClient.call_args == mocker.call(
            hostname=fake_hostname,
            target=expected_target,
            auth=amqp_token_mock,
            keep_alive_interval=120,
            transport_type=TransportType.Amqp,
        )

    @pytest.mark.it(
        "Creates a JWTTokenAuth instance with the correct parameters and uses it to create an AMQP SendClient if no token scope is provided (uses the default scope of 'https://iothubs.azure.net/.default')"
    )
    def test_create_JWTTokenAuth_with_bearer_token_default_scope(
        self, mocker, mock_azure_identity_TokenCredential, mock_SendClient
    ):
        amqp_token_init_mock = mocker.patch("azure.iot.hub.iothub_amqp_client.JWTTokenAuth")
        amqp_token_mock = amqp_token_init_mock.return_value

        IoTHubAmqpClientTokenAuth(fake_hostname, mock_azure_identity_TokenCredential)

        # JWTTokenAuth Creation
        assert amqp_token_init_mock.call_count == 1
        _, kwargs = amqp_token_init_mock.call_args
        assert kwargs["uri"] == "https://" + fake_hostname
        assert kwargs["audience"] == "https://iothubs.azure.net/.default"
        assert callable(kwargs["get_token"])
        assert kwargs["token_type"] == b"bearer"

        # AMQP SendClient is created
        assert mock_SendClient.call_count == 1
        assert mock_SendClient.call_args == mocker.call(
            hostname=fake_hostname,
            target=expected_target,
            auth=amqp_token_mock,
            keep_alive_interval=120,
            transport_type=TransportType.Amqp,
        )

    @pytest.mark.it(
        "Creates a JWTTokenAuth instance with the correct parameters and uses it to create an AMQP over WebSocket SendClient if no token scope is provided (uses the default scope of 'https://iothubs.azure.net/.default')"
    )
    def test_create_JWTTokenAuth_with_bearer_token_default_scope_AmqpOverWebsocket(
        self, mocker, mock_azure_identity_TokenCredential, mock_SendClient
    ):
        amqp_token_init_mock = mocker.patch("azure.iot.hub.iothub_amqp_client.JWTTokenAuth")
        amqp_token_mock = amqp_token_init_mock.return_value

        IoTHubAmqpClientTokenAuth(
            fake_hostname,
            mock_azure_identity_TokenCredential,
            transport_type=TransportType.AmqpOverWebsocket,
        )

        # JWTTokenAuth Creation
        assert amqp_token_init_mock.call_count == 1
        _, kwargs = amqp_token_init_mock.call_args
        assert kwargs["uri"] == "https://" + fake_hostname
        assert kwargs["audience"] == "https://iothubs.azure.net/.default"
        assert callable(kwargs["get_token"])
        assert kwargs["token_type"] == b"bearer"

        # AMQP over Websocket SendClient is created
        assert mock_SendClient.call_count == 1
        assert mock_SendClient.call_args == mocker.call(
            hostname=fake_hostname,
            target=expected_target,
            auth=amqp_token_mock,
            keep_alive_interval=120,
            transport_type=TransportType.AmqpOverWebsocket,
        )

    @pytest.mark.it(
        "Retrieves the token from the azure-identity TokenCredential using the specified token scope"
    )
    def test_retrieve_token_from_azure_identity(self, mocker, mock_azure_identity_TokenCredential):
        amqp_token_init_mock = mocker.patch("azure.iot.hub.iothub_amqp_client.JWTTokenAuth")

        IoTHubAmqpClientTokenAuth(
            fake_hostname, mock_azure_identity_TokenCredential, fake_token_scope
        )
        get_token = amqp_token_init_mock.call_args.kwargs["get_token"]
        get_token()
        mock_azure_identity_TokenCredential.get_token.assert_called_once_with(fake_token_scope)


@pytest.mark.describe("IoTHubAmqpClientTokenAuth - .send_message_to_device()")
class TestIoTHubAmqpClientTokenAuthSendMessageToDevice(
    IoTHubAmqpClientTokenAuthTestConfig, SharedIotHubAmqpClientSendMessageToDeviceTests
):
    pass


@pytest.mark.describe("IoTHubAmqpClientTokenAuth - .disconnect_sync()")
class TestIoTHubAmqpClientTokenAuthDisconnectSync(
    IoTHubAmqpClientTokenAuthTestConfig, SharedIotHubAmqpClientDisconnectSyncTests
):
    pass


@pytest.mark.describe("CBS response settlement")
class TestCbsResponseSettlement:
    @pytest.mark.it("Acknowledges unsettled CBS responses without changing authentication results")
    @pytest.mark.parametrize("settled", [False, None, True])
    @pytest.mark.parametrize(
        "status_code, expected_result",
        [
            (200, ManagementExecuteOperationResult.OK),
            (401, ManagementExecuteOperationResult.FAILED_BAD_STATUS),
        ],
    )
    def test_response_settlement(self, mocker, settled, status_code, expected_result):
        session = mocker.MagicMock()

        def create_receiver(endpoint, **kwargs):
            return ReceiverLink(session, 0, endpoint, network_trace_params={}, **kwargs)

        session.create_receiver_link.side_effect = create_receiver
        management = ManagementLink(
            session,
            "$cbs",
            status_code_field=b"status-code",
            status_description_field=b"status-description",
        )
        decoder = mocker.patch("azure.iot.hub._pyamqp.receiver.decode_payload")

        for delivery_id in (0, 1):
            session._outgoing_disposition.reset_mock()
            request_id = "request-{}".format(delivery_id)
            callback = mocker.Mock()
            request = Message(properties=Properties(message_id=request_id))
            management._pending_operations.append(PendingManagementOperation(request, callback))
            response = Message(
                properties=Properties(correlation_id=request_id),
                application_properties={
                    b"status-code": status_code,
                    b"status-description": "response",
                },
            )
            decoder.return_value = response
            frame = TransferFrame(
                handle=0,
                delivery_id=delivery_id,
                delivery_tag=str(delivery_id).encode(),
                settled=settled,
                more=False,
                payload=b"response",
            )

            management._response_link._incoming_transfer(frame)

            callback.assert_called_once_with(
                expected_result, status_code, "response", response, None
            )
            assert management._pending_operations == []
            if settled:
                session._outgoing_disposition.assert_not_called()
            else:
                session._outgoing_disposition.assert_called_once()
                disposition = session._outgoing_disposition.call_args.args[0]
                assert disposition.role == Role.Receiver
                assert disposition.first == delivery_id
                assert disposition.settled is True
                assert isinstance(disposition.state, Accepted)
                assert frame.delivery_tag not in management._response_link._received_delivery_tags
