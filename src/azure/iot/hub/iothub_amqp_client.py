# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import base64
import time
import hashlib
import hmac
from uuid import uuid4
from urllib import parse as urllib_parse
from azure.core.credentials import AccessToken

from ._pyamqp import SendClient
from ._pyamqp.authentication import JWTTokenAuth
from ._pyamqp.constants import TransportType
from ._pyamqp.error import AMQPException
from ._pyamqp.message import Message, Properties


default_sas_expiry = 3600


class C2DMessageSendError(Exception):
    """Raised when a cloud-to-device message fails to send."""


class IoTHubAmqpClientBase:
    def disconnect_sync(self):
        """
        Disconnect the Amqp client.
        """
        if self.amqp_client:
            self.amqp_client.close()
            self.amqp_client = None

    def send_message_to_device(self, device_id, message, app_props):
        """Send a message to the specified deivce.

        :param str device_id: The name (Id) of the device.
        :param str message: The message that is to be delivered to the device.
        :param dict app_props: Application and system properties for the message

        :raises: Exception if the Send command is not able to send the message
        """
        properties_kwargs = {
            "message_id": str(uuid4()),
            "to": "/devices/{}/messages/devicebound".format(device_id),
        }
        app_properties = {}

        for prop_key, prop_value in app_props.items():
            if prop_key == "contentType":
                properties_kwargs["content_type"] = prop_value
            elif prop_key == "contentEncoding":
                properties_kwargs["content_encoding"] = prop_value
            elif prop_key == "correlationId":
                properties_kwargs["correlation_id"] = prop_value
            elif prop_key == "expiryTimeUtc":
                properties_kwargs["absolute_expiry_time"] = prop_value
            elif prop_key == "messageId":
                properties_kwargs["message_id"] = prop_value
            else:
                app_properties[prop_key] = prop_value

        msg_body = message.encode("utf-8") if isinstance(message, str) else message
        amqp_message = Message(
            properties=Properties(**properties_kwargs),
            application_properties=app_properties,
            data=[msg_body],
        )

        try:
            self.amqp_client.send_message(amqp_message)
        except AMQPException:
            raise C2DMessageSendError("C2D message send failure")


class IoTHubAmqpClientSharedAccessKeyAuth(IoTHubAmqpClientBase):
    def __init__(self, hostname, shared_access_key_name, shared_access_key, transport_type=TransportType.Amqp):
        def get_token():
            expiry = int(time.time() + default_sas_expiry)
            sas = base64.b64decode(shared_access_key)
            string_to_sign = (hostname + "\n" + str(expiry)).encode("utf-8")
            signed_hmac_sha256 = hmac.HMAC(sas, string_to_sign, hashlib.sha256)
            signature = urllib_parse.quote(base64.b64encode(signed_hmac_sha256.digest()))
            return AccessToken(
                "SharedAccessSignature sr={}&sig={}&se={}&skn={}".format(
                    hostname, signature, expiry, shared_access_key_name
                ),
                expiry,
            )

        auth = JWTTokenAuth(
            uri="https://" + hostname,
            audience="https://" + hostname,
            get_token=get_token,
            token_type=b"servicebus.windows.net:sastoken",
        )
        self.amqp_client = SendClient(
            hostname=hostname,
            target="amqps://" + hostname + "/messages/devicebound",
            auth=auth,
            keep_alive_interval=120,
            transport_type=transport_type,
        )


class IoTHubAmqpClientTokenAuth(IoTHubAmqpClientBase):
    def __init__(
        self, hostname, token_credential, token_scope="https://iothubs.azure.net/.default", transport_type=TransportType.Amqp
    ):
        def get_token():
            result = token_credential.get_token(token_scope)
            return AccessToken("Bearer " + result.token, result.expires_on)

        auth = JWTTokenAuth(
            uri="https://" + hostname,
            audience=token_scope,
            get_token=get_token,
            token_type=b"bearer",
        )
        self.amqp_client = SendClient(
            hostname=hostname,
            target="amqps://" + hostname + "/messages/devicebound",
            auth=auth,
            keep_alive_interval=120,
            transport_type=transport_type,
        )
