"""
A small pytest plugin that shows the a concise help string that only contains
the options defined by the plugins defined in execution-spec-tests.
"""

import argparse
from pathlib import Path

import pytest


def pytest_addoption(parser):
    """Add command-line options to pytest for specific help commands."""
    help_group = parser.getgroup("help_options", "Help options for different commands")
    help_group.addoption(
        "--check-eip-versions-help",
        action="store_true",
        dest="show_check_eip_versions_help",
        default=False,
        help="Show help options only for the check_eip_versions command and exit.",
    )
    help_group.addoption(
        "--fill-help",
        action="store_true",
        dest="show_fill_help",
        default=False,
        help="Show help options only for the fill command and exit.",
    )
    help_group.addoption(
        "--consume-help",
        action="store_true",
        dest="show_consume_help",
        default=False,
        help="Show help options specific to the consume command and exit.",
    )
    help_group.addoption(
        "--execute-remote-help",
        action="store_true",
        dest="show_execute_help",
        default=False,
        help="Show help options specific to the execute's command remote and exit.",
    )
    help_group.addoption(
        "--execute-hive-help",
        action="store_true",
        dest="show_execute_hive_help",
        default=False,
        help="Show help options specific to the execute's command hive and exit.",
    )
    help_group.addoption(
        "--execute-recover-help",
        action="store_true",
        dest="show_execute_recover_help",
        default=False,
        help="Show help options specific to the execute's command recover and exit.",
    )
    help_group.addoption(
        "--execute-eth-config-help",
        action="store_true",
        dest="show_execute_eth_config_help",
        default=False,
        help="Show help options specific to the execute's command eth_config and exit.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Handle specific help flags by displaying the corresponding help message."""
    if config.getoption("show_check_eip_versions_help"):
        show_specific_help(
            config,
            "pytest-check-eip-versions.ini",
            [
                "spec_version_checker",
                "EIP spec version",
            ],
        )
    elif config.getoption("show_fill_help"):
        show_specific_help(
            config,
            "pytest-fill.ini",
            [
                "evm",
                "solc",
                "fork range",
                "filler location",
                "defining debug",
                "pre-allocation behavior during test filling",
                "ported",
            ],
        )
    elif config.getoption("show_consume_help"):
        show_specific_help(
            config,
            "pytest-consume.ini",
            [
                "consuming",
            ],
        )
    elif config.getoption("show_execute_help"):
        show_specific_help(
            config,
            "pytest-execute.ini",
            [
                "execute",
                "remote RPC configuration",
                "pre-allocation behavior during test execution",
                "sender key fixtures",
                "remote seed sender",
            ],
        )
    elif config.getoption("show_execute_hive_help"):
        show_specific_help(
            config,
            "pytest-execute-hive.ini",
            [
                "execute",
                "hive RPC client",
                "pre-allocation behavior during test execution",
                "sender key fixtures",
                "remote seed sender",
            ],
        )
    elif config.getoption("show_execute_recover_help"):
        show_specific_help(
            config,
            "pytest-execute-recover.ini",
            [
                "fund recovery",
                "remote RPC configuration",
                "remote seed sender",
            ],
        )
    elif config.getoption("show_execute_eth_config_help"):
        show_specific_help(
            config,
            "pytest-execute-eth-config.ini",
            [
                "eth_config",
            ],
        )


def show_specific_help(config, expected_ini, substrings):
    """Print help options filtered by specific substrings from the given configuration."""
    pytest_ini = Path(config.inifile)
    if pytest_ini.name != expected_ini:
        raise ValueError(
            f"Unexpected {expected_ini}!={pytest_ini.name} file option generating help."
        )

    test_parser = argparse.ArgumentParser()
    for group in config._parser.optparser._action_groups:
        if any(substring in group.title for substring in substrings):
            new_group = test_parser.add_argument_group(group.title, group.description)
            for action in group._group_actions:
                kwargs = {
                    "default": action.default,
                    "help": action.help,
                    "required": action.required,
                }
                if isinstance(action, argparse._StoreTrueAction):
                    kwargs["action"] = "store_true"
                else:
                    kwargs["type"] = action.type
                if action.nargs:
                    kwargs["nargs"] = action.nargs
                new_group.add_argument(*action.option_strings, **kwargs)

    print(test_parser.format_help())
    pytest.exit("After displaying help.", returncode=pytest.ExitCode.OK)
