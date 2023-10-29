#!/usr/bin/env python

"""Tests for `kicad_auto_silkscreen` package."""


import unittest
from click.testing import CliRunner

from kicad_auto_silkscreen import kicad_auto_silkscreen
from kicad_auto_silkscreen import cli


class TestKicad_auto_silkscreen(unittest.TestCase):
    """Tests for `kicad_auto_silkscreen` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'kicad_auto_silkscreen.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output
