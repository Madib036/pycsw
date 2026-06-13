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
"""Unit tests for pycsw.core.admin"""

import os
import tempfile
from configparser import ConfigParser
from unittest import mock

import pytest

import pycsw.core.admin as admin
from pycsw.core import repository

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Tests for repo_config dict-based Repository construction
# ---------------------------------------------------------------------------

class TestRepoConfigDictConstruction:
    """Tests that admin functions build the correct repo_config dict."""

    def test_load_records_passes_dict_to_repository(self, tmp_path):
        """load_records constructs a repo_config dict with 'database' and 'table' keys."""
        database = 'sqlite:///test.db'
        table = 'records'

        with mock.patch('pycsw.core.admin.repository.Repository') as mock_repo_cls, \
             mock.patch('pycsw.core.admin.os.path.isfile', return_value=False), \
             mock.patch('pycsw.core.admin.glob', return_value=[]):

            mock_repo = mock.MagicMock()
            mock_repo_cls.return_value = mock_repo

            context = mock.MagicMock()

            admin.load_records(context, database, table, str(tmp_path))

            mock_repo_cls.assert_called_once()
            call_args = mock_repo_cls.call_args
            repo_config = call_args[0][0]

            assert isinstance(repo_config, dict)
            assert repo_config['database'] == database
            assert repo_config['table'] == table

    def test_export_records_passes_dict_to_repository(self, tmp_path):
        """export_records constructs a repo_config dict with 'database' and 'table' keys."""
        database = 'sqlite:///test.db'
        table = 'records'

        mock_session = mock.MagicMock()
        mock_session.query.return_value.count.return_value = 0
        mock_session.query.return_value.all.return_value = []

        with mock.patch('pycsw.core.admin.repository.Repository') as mock_repo_cls:
            mock_repo = mock.MagicMock()
            mock_repo.session = mock_session
            mock_repo_cls.return_value = mock_repo

            context = mock.MagicMock()

            admin.export_records(context, database, table, str(tmp_path))

            mock_repo_cls.assert_called_once()
            call_args = mock_repo_cls.call_args
            repo_config = call_args[0][0]

            assert isinstance(repo_config, dict)
            assert repo_config['database'] == database
            assert repo_config['table'] == table

    def test_gen_sitemap_passes_dict_to_repository(self, tmp_path):
        """gen_sitemap constructs a repo_config dict with 'database' and 'table' keys."""
        database = 'sqlite:///test.db'
        table = 'records'
        url = 'http://example.org/csw'
        output_file = str(tmp_path / 'sitemap.xml')

        with mock.patch('pycsw.core.admin.repository.Repository') as mock_repo_cls, \
             mock.patch('pycsw.core.admin.etree.Element'), \
             mock.patch('pycsw.core.admin.etree.tostring', return_value=b'<xml/>'), \
             mock.patch('builtins.open', mock.mock_open()):

            mock_repo = mock.MagicMock()
            mock_repo.query.return_value = (0, [])
            mock_repo_cls.return_value = mock_repo

            context = mock.MagicMock()
            context.namespaces = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                                  'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

            admin.gen_sitemap(context, database, table, url, output_file)

            mock_repo_cls.assert_called_once()
            call_args = mock_repo_cls.call_args
            repo_config = call_args[0][0]

            assert isinstance(repo_config, dict)
            assert repo_config['database'] == database
            assert repo_config['table'] == table

    def test_refresh_harvested_records_passes_dict_to_repository(self):
        """refresh_harvested_records constructs a repo_config dict."""
        database = 'sqlite:///test.db'
        table = 'records'
        url = 'http://example.org/csw'

        with mock.patch('pycsw.core.admin.repository.Repository') as mock_repo_cls:
            mock_repo = mock.MagicMock()
            mock_repo.query.return_value = (0, [])
            mock_repo_cls.return_value = mock_repo

            context = mock.MagicMock()

            admin.refresh_harvested_records(context, database, table, url)

            mock_repo_cls.assert_called_once()
            call_args = mock_repo_cls.call_args
            repo_config = call_args[0][0]

            assert isinstance(repo_config, dict)
            assert repo_config['database'] == database
            assert repo_config['table'] == table


# ---------------------------------------------------------------------------
# Tests for post_xml
# ---------------------------------------------------------------------------

class TestPostXml:
    """Tests for the post_xml function."""

    def test_post_xml_returns_text_from_http_post(self, tmp_path):
        """post_xml returns the .text attribute of the http_post response."""
        xml_file = tmp_path / 'request.xml'
        xml_file.write_text('<GetCapabilities/>')

        mock_response = mock.MagicMock()
        mock_response.text = '<Capabilities>response</Capabilities>'

        with mock.patch('pycsw.core.admin.http_post', return_value=mock_response) as mock_post:
            result = admin.post_xml('http://example.org/csw', str(xml_file))

        assert result == '<Capabilities>response</Capabilities>'
        mock_post.assert_called_once_with(
            url='http://example.org/csw',
            request='<GetCapabilities/>',
            timeout=30
        )

    def test_post_xml_uses_custom_timeout(self, tmp_path):
        """post_xml passes the timeout parameter to http_post."""
        xml_file = tmp_path / 'request.xml'
        xml_file.write_text('<GetCapabilities/>')

        mock_response = mock.MagicMock()
        mock_response.text = 'response'

        with mock.patch('pycsw.core.admin.http_post', return_value=mock_response) as mock_post:
            admin.post_xml('http://example.org/csw', str(xml_file), timeout=60)

        mock_post.assert_called_once_with(
            url='http://example.org/csw',
            request='<GetCapabilities/>',
            timeout=60
        )

    def test_post_xml_raises_runtime_error_on_failure(self, tmp_path):
        """post_xml wraps exceptions in RuntimeError."""
        xml_file = tmp_path / 'request.xml'
        xml_file.write_text('<GetCapabilities/>')

        with mock.patch('pycsw.core.admin.http_post', side_effect=Exception('network error')):
            with pytest.raises(RuntimeError):
                admin.post_xml('http://example.org/csw', str(xml_file))

    def test_post_xml_raises_runtime_error_on_missing_file(self):
        """post_xml wraps file-not-found error in RuntimeError."""
        with pytest.raises(RuntimeError):
            admin.post_xml('http://example.org/csw', '/nonexistent/file.xml')


# ---------------------------------------------------------------------------
# Tests for cli_migrate_config federatedcatalogues handling
# ---------------------------------------------------------------------------

class TestCliMigrateConfigFederatedCatalogues:
    """Tests for federatedcatalogues migration in cli_migrate_config."""

    def _make_ini_config(self, tmp_path, federatedcatalogues=None):
        """Helper to create a minimal INI config file."""
        content = '[server]\nhostname=localhost\nurl=http://localhost/csw\n'
        if federatedcatalogues:
            content += f'federatedcatalogues={federatedcatalogues}\n'
        content += '[metadata:main]\n'
        content += '[manager]\ntransactions=false\n'
        content += '[repository]\ndatabase=sqlite:///test.db\ntable=records\n'
        content += '[metadata:inspire]\n'

        config_file = tmp_path / 'pycsw.cfg'
        config_file.write_text(content)
        return str(config_file)

    def test_migrate_config_federatedcatalogues_single_url(self, tmp_path):
        """federatedcatalogues single URL is stored as a list."""
        config_file = self._make_ini_config(
            tmp_path,
            federatedcatalogues='http://catalog.data.gov/csw'
        )

        captured = {}

        def mock_yaml_dump(data, filepath):
            captured['data'] = data

        with mock.patch('pycsw.core.admin.yaml_dump', side_effect=mock_yaml_dump), \
             mock.patch('pycsw.core.admin.click.echo'):
            from click.testing import CliRunner
            runner = CliRunner()
            result = runner.invoke(admin.cli_migrate_config, ['--config', config_file])

        assert 'data' in captured
        assert 'federatedcatalogues' in captured['data']
        assert isinstance(captured['data']['federatedcatalogues'], list)
        assert 'http://catalog.data.gov/csw' in captured['data']['federatedcatalogues']

    def test_migrate_config_federatedcatalogues_multiple_urls(self, tmp_path):
        """federatedcatalogues comma-separated URLs are stored as a list."""
        config_file = self._make_ini_config(
            tmp_path,
            federatedcatalogues='http://catalog1.example.org/csw,http://catalog2.example.org/csw'
        )

        captured = {}

        def mock_yaml_dump(data, filepath):
            captured['data'] = data

        with mock.patch('pycsw.core.admin.yaml_dump', side_effect=mock_yaml_dump), \
             mock.patch('pycsw.core.admin.click.echo'):
            from click.testing import CliRunner
            runner = CliRunner()
            result = runner.invoke(admin.cli_migrate_config, ['--config', config_file])

        assert 'data' in captured
        urls = captured['data']['federatedcatalogues']
        assert isinstance(urls, list)
        assert len(urls) == 2
        assert 'http://catalog1.example.org/csw' in urls
        assert 'http://catalog2.example.org/csw' in urls

    def test_migrate_config_federatedcatalogues_is_list_not_nested_dict(self, tmp_path):
        """Migrated federatedcatalogues is a flat list, not a nested dict with catalogues."""
        config_file = self._make_ini_config(
            tmp_path,
            federatedcatalogues='http://catalog.data.gov/csw'
        )

        captured = {}

        def mock_yaml_dump(data, filepath):
            captured['data'] = data

        with mock.patch('pycsw.core.admin.yaml_dump', side_effect=mock_yaml_dump), \
             mock.patch('pycsw.core.admin.click.echo'):
            from click.testing import CliRunner
            runner = CliRunner()
            runner.invoke(admin.cli_migrate_config, ['--config', config_file])

        assert 'data' in captured
        # Must be a flat list of URLs, not a dict with 'catalogues' key
        fedcat = captured['data']['federatedcatalogues']
        assert isinstance(fedcat, list)
        assert not isinstance(fedcat[0], dict)

    def test_migrate_config_no_federatedcatalogues_produces_empty_list(self, tmp_path):
        """When no federatedcatalogues in config, output has empty list."""
        config_file = self._make_ini_config(tmp_path)

        captured = {}

        def mock_yaml_dump(data, filepath):
            captured['data'] = data

        with mock.patch('pycsw.core.admin.yaml_dump', side_effect=mock_yaml_dump), \
             mock.patch('pycsw.core.admin.click.echo'):
            from click.testing import CliRunner
            runner = CliRunner()
            runner.invoke(admin.cli_migrate_config, ['--config', config_file])

        assert 'data' in captured
        assert 'federatedcatalogues' in captured['data']
        assert captured['data']['federatedcatalogues'] == []

    def test_migrate_config_no_distributedsearch_key_in_output(self, tmp_path):
        """Migrated config must not contain the old 'distributedsearch' key."""
        config_file = self._make_ini_config(
            tmp_path,
            federatedcatalogues='http://catalog.data.gov/csw'
        )

        captured = {}

        def mock_yaml_dump(data, filepath):
            captured['data'] = data

        with mock.patch('pycsw.core.admin.yaml_dump', side_effect=mock_yaml_dump), \
             mock.patch('pycsw.core.admin.click.echo'):
            from click.testing import CliRunner
            runner = CliRunner()
            runner.invoke(admin.cli_migrate_config, ['--config', config_file])

        assert 'data' in captured
        assert 'distributedsearch' not in captured['data']