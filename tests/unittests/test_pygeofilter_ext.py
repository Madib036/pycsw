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
"""Unit tests for pycsw.core.pygeofilter_ext"""

from unittest import mock

import pytest

from pycsw.core.pygeofilter_ext import PycswCSWFES11Parser, PycswFilterEvaluator, to_filter

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Tests for PycswCSWFES11Parser
# ---------------------------------------------------------------------------

class TestPycswCSWFES11Parser:
    """Tests for the PycswCSWFES11Parser class added in the PR."""

    def test_parser_is_subclass_of_fes11parser(self):
        """PycswCSWFES11Parser is a subclass of FES11Parser."""
        from pygeofilter.parsers.fes.v11 import FES11Parser
        assert issubclass(PycswCSWFES11Parser, FES11Parser)

    def test_parse_delegates_to_new_fes11parser_instance(self):
        """PycswCSWFES11Parser.parse() creates a new FES11Parser and delegates."""
        from pygeofilter.parsers.fes.v11 import FES11Parser

        parser = PycswCSWFES11Parser()
        mock_ast = mock.MagicMock()

        with mock.patch.object(FES11Parser, 'parse', return_value=mock_ast) as mock_parse:
            result = parser.parse('<Filter/>')

        mock_parse.assert_called_once_with('<Filter/>')
        assert result is mock_ast

    def test_parse_creates_fresh_instance_each_call(self):
        """PycswCSWFES11Parser.parse() uses a fresh FES11Parser per call."""
        from pygeofilter.parsers.fes.v11 import FES11Parser

        parser = PycswCSWFES11Parser()
        mock_ast1 = mock.MagicMock()
        mock_ast2 = mock.MagicMock()

        with mock.patch.object(FES11Parser, 'parse',
                                side_effect=[mock_ast1, mock_ast2]) as mock_parse:
            result1 = parser.parse('<Filter1/>')
            result2 = parser.parse('<Filter2/>')

        assert mock_parse.call_count == 2
        assert result1 is mock_ast1
        assert result2 is mock_ast2

    def test_parse_passes_input_unchanged(self):
        """PycswCSWFES11Parser.parse() passes the input unchanged to FES11Parser."""
        from pygeofilter.parsers.fes.v11 import FES11Parser

        parser = PycswCSWFES11Parser()
        test_input = b'<Filter><PropertyIsEqualTo/></Filter>'

        with mock.patch.object(FES11Parser, 'parse', return_value=None) as mock_parse:
            parser.parse(test_input)

        mock_parse.assert_called_once_with(test_input)

    def test_parse_returns_none_when_fes11_returns_none(self):
        """PycswCSWFES11Parser.parse() returns None when FES11Parser.parse() returns None."""
        from pygeofilter.parsers.fes.v11 import FES11Parser

        parser = PycswCSWFES11Parser()

        with mock.patch.object(FES11Parser, 'parse', return_value=None):
            result = parser.parse('')

        assert result is None


# ---------------------------------------------------------------------------
# Tests for PycswFilterEvaluator
# ---------------------------------------------------------------------------

class TestPycswFilterEvaluator:
    """Tests for the PycswFilterEvaluator class (ilike dbtype handling)."""

    def test_evaluator_stores_dbtype(self):
        """PycswFilterEvaluator stores the dbtype attribute."""
        evaluator = PycswFilterEvaluator(field_mapping={}, dbtype='sqlite')
        assert evaluator._pycsw_dbtype == 'sqlite'

    def test_evaluator_defaults_to_sqlite(self):
        """PycswFilterEvaluator defaults to sqlite dbtype."""
        evaluator = PycswFilterEvaluator()
        assert evaluator._pycsw_dbtype == 'sqlite'

    def test_evaluator_stores_postgresql_dbtype(self):
        """PycswFilterEvaluator can be initialized with postgresql dbtype."""
        evaluator = PycswFilterEvaluator(field_mapping={}, dbtype='postgresql')
        assert evaluator._pycsw_dbtype == 'postgresql'

    def test_evaluator_stores_postgis_native_dbtype(self):
        """PycswFilterEvaluator can be initialized with postgresql+postgis+native dbtype."""
        evaluator = PycswFilterEvaluator(
            field_mapping={}, dbtype='postgresql+postgis+native'
        )
        assert evaluator._pycsw_dbtype == 'postgresql+postgis+native'


# ---------------------------------------------------------------------------
# Tests for to_filter factory function
# ---------------------------------------------------------------------------

class TestToFilter:
    """Tests for the to_filter factory function."""

    def test_to_filter_creates_evaluator_with_correct_dbtype(self):
        """to_filter creates a PycswFilterEvaluator with the given dbtype."""
        mock_ast = mock.MagicMock()

        with mock.patch(
            'pycsw.core.pygeofilter_ext.PycswFilterEvaluator'
        ) as mock_evaluator_cls:
            mock_evaluator = mock.MagicMock()
            mock_evaluator_cls.return_value = mock_evaluator
            mock_evaluator.evaluate.return_value = mock.MagicMock()

            to_filter(mock_ast, 'postgresql', field_mapping={'key': 'val'})

            mock_evaluator_cls.assert_called_once_with({'key': 'val'}, 'postgresql')

    def test_to_filter_calls_evaluate_on_ast(self):
        """to_filter calls evaluate(ast) on the PycswFilterEvaluator instance."""
        mock_ast = mock.MagicMock()
        mock_filter_result = mock.MagicMock()

        with mock.patch(
            'pycsw.core.pygeofilter_ext.PycswFilterEvaluator'
        ) as mock_evaluator_cls:
            mock_evaluator = mock.MagicMock()
            mock_evaluator_cls.return_value = mock_evaluator
            mock_evaluator.evaluate.return_value = mock_filter_result

            result = to_filter(mock_ast, 'sqlite')

        mock_evaluator.evaluate.assert_called_once_with(mock_ast)
        assert result is mock_filter_result

    def test_to_filter_passes_none_field_mapping_by_default(self):
        """to_filter passes None as field_mapping when not specified."""
        mock_ast = mock.MagicMock()

        with mock.patch(
            'pycsw.core.pygeofilter_ext.PycswFilterEvaluator'
        ) as mock_evaluator_cls:
            mock_evaluator = mock.MagicMock()
            mock_evaluator_cls.return_value = mock_evaluator
            mock_evaluator.evaluate.return_value = mock.MagicMock()

            to_filter(mock_ast, 'sqlite')

            mock_evaluator_cls.assert_called_once_with(None, 'sqlite')