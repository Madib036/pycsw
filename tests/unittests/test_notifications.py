# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2025 Tom Kralidis
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================
"""Unit tests for pycsw.notifications"""

import importlib
import sys
from unittest import mock

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Tests for CLIENTS registry
# ---------------------------------------------------------------------------

class TestClientsRegistry:
    """Tests for the CLIENTS dictionary in pycsw.notifications."""

    @pytest.fixture(autouse=True)
    def patch_broker_import(self):
        """Patch away the pycsw.broker.base import so the module loads."""
        mock_broker_base = mock.MagicMock()
        mock_broker_base.BasePubSubClient = mock.MagicMock

        with mock.patch.dict(sys.modules, {
            'pycsw.broker': mock.MagicMock(),
            'pycsw.broker.base': mock_broker_base,
        }):
            # Force re-import with mocked broker
            if 'pycsw.notifications' in sys.modules:
                del sys.modules['pycsw.notifications']
            import pycsw.notifications as notifications_mod
            self.notifications = notifications_mod
            yield

    def test_clients_dict_has_mqtt_key(self):
        """CLIENTS dict contains an 'mqtt' entry."""
        assert 'mqtt' in self.notifications.CLIENTS

    def test_clients_dict_has_http_key(self):
        """CLIENTS dict contains an 'http' entry."""
        assert 'http' in self.notifications.CLIENTS

    def test_clients_mqtt_points_to_mqtt_client(self):
        """CLIENTS['mqtt'] points to the MQTT client class path."""
        assert 'MQTTPubSubClient' in self.notifications.CLIENTS['mqtt']

    def test_clients_http_points_to_http_client(self):
        """CLIENTS['http'] points to the HTTP client class path."""
        assert 'HTTPPubSubClient' in self.notifications.CLIENTS['http']

    def test_clients_dict_has_exactly_two_entries(self):
        """CLIENTS dict has exactly two client type entries."""
        assert len(self.notifications.CLIENTS) == 2

    def test_clients_values_are_dotted_module_paths(self):
        """Each CLIENTS value is a dotted module path (contains a dot)."""
        for client_type, class_path in self.notifications.CLIENTS.items():
            assert '.' in class_path, (
                f"CLIENTS['{client_type}'] = '{class_path}' is not a dotted module path"
            )

    def test_clients_values_rsplit_on_last_dot(self):
        """Each CLIENTS value can be split into module path and class name."""
        for client_type, class_path in self.notifications.CLIENTS.items():
            parts = class_path.rsplit('.', 1)
            assert len(parts) == 2, (
                f"CLIENTS['{client_type}'] = '{class_path}' cannot be split into module + class"
            )
            module_path, class_name = parts
            assert module_path, f"Module path for '{client_type}' is empty"
            assert class_name, f"Class name for '{client_type}' is empty"


# ---------------------------------------------------------------------------
# Tests for load_client function
# ---------------------------------------------------------------------------

class TestLoadClient:
    """Tests for the load_client function in pycsw.notifications."""

    @pytest.fixture(autouse=True)
    def patch_broker_import(self):
        """Patch away pycsw.broker.base so the module can be imported."""
        mock_broker_base = mock.MagicMock()
        mock_broker_base.BasePubSubClient = mock.MagicMock

        with mock.patch.dict(sys.modules, {
            'pycsw.broker': mock.MagicMock(),
            'pycsw.broker.base': mock_broker_base,
        }):
            if 'pycsw.notifications' in sys.modules:
                del sys.modules['pycsw.notifications']
            import pycsw.notifications as notifications_mod
            self.notifications = notifications_mod
            yield

    def test_load_client_calls_importlib_import_module(self):
        """load_client uses importlib.import_module to load the client module."""
        mock_client_instance = mock.MagicMock()
        mock_client_class = mock.MagicMock(return_value=mock_client_instance)
        mock_module = mock.MagicMock()
        mock_module.MQTTPubSubClient = mock_client_class

        def_ = {'type': 'mqtt', 'url': 'mqtt://localhost', 'channel': 'test'}

        with mock.patch('pycsw.notifications.importlib.import_module',
                        return_value=mock_module) as mock_import:
            result = self.notifications.load_client(def_)

        expected_module_path = self.notifications.CLIENTS['mqtt'].rsplit('.', 1)[0]
        mock_import.assert_called_once_with(expected_module_path)

    def test_load_client_instantiates_correct_class(self):
        """load_client instantiates the class specified in CLIENTS."""
        mock_client_instance = mock.MagicMock()
        mock_client_class = mock.MagicMock(return_value=mock_client_instance)
        mock_module = mock.MagicMock()
        mock_module.HTTPPubSubClient = mock_client_class

        def_ = {'type': 'http', 'url': 'http://localhost', 'channel': 'test'}

        with mock.patch('pycsw.notifications.importlib.import_module',
                        return_value=mock_module):
            result = self.notifications.load_client(def_)

        mock_client_class.assert_called_once_with(def_)
        assert result is mock_client_instance

    def test_load_client_passes_def_dict_to_constructor(self):
        """load_client passes the full def_ dict to the client class constructor."""
        mock_client_class = mock.MagicMock()
        mock_module = mock.MagicMock()
        mock_module.MQTTPubSubClient = mock_client_class

        def_ = {
            'type': 'mqtt',
            'url': 'mqtt://broker.example.org:1883',
            'channel': 'test/channel',
            'show_link': True
        }

        with mock.patch('pycsw.notifications.importlib.import_module',
                        return_value=mock_module):
            self.notifications.load_client(def_)

        mock_client_class.assert_called_once_with(def_)

    def test_load_client_raises_on_unknown_type(self):
        """load_client raises KeyError for an unknown client type."""
        def_ = {'type': 'unknown_protocol', 'url': 'unknown://localhost'}

        with pytest.raises(KeyError):
            self.notifications.load_client(def_)

    def test_load_client_http_type(self):
        """load_client works correctly for 'http' type."""
        mock_client_instance = mock.MagicMock()
        mock_client_class = mock.MagicMock(return_value=mock_client_instance)
        mock_module = mock.MagicMock()
        mock_module.HTTPPubSubClient = mock_client_class

        def_ = {'type': 'http', 'url': 'http://api.example.org/notify', 'channel': 'records'}

        with mock.patch('pycsw.notifications.importlib.import_module',
                        return_value=mock_module):
            result = self.notifications.load_client(def_)

        assert result is mock_client_instance