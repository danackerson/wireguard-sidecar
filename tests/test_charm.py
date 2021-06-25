# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest

from charm import WireguardSidecarCharm
from ops.model import ActiveStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(WireguardSidecarCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_wireguard_pebble_ready(self):
        # Check the initial Pebble plan is empty
        initial_plan = self.harness.get_container_pebble_plan("wireguard")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Expected plan after Pebble ready with default config
        expected_plan = {
            "summary": "wireguard layer",
            "description": "pebble config layer for wireguard",
            "services": {
                "wireguard": {
                    "override": "replace",
                    "summary": "wireguard",
                    "command": "/scripts/run",
                    "startup": "enabled",
                    "environment": {
                        "server_port": self.harness.charm.model.config["server_port"]
                    },
                }
            },
        }
        # Get the wireguard container from the model
        container = self.harness.model.unit.get_container("wireguard")
        # Emit the PebbleReadyEvent carrying the wireguard container
        self.harness.charm.on.wireguard_pebble_ready.emit(container)
        # Get the plan now we've run PebbleReady
        updated_plan = self.harness.get_container_pebble_plan("wireguard").to_dict()
        # Check we've got the plan we expected
        self.assertEqual(expected_plan, updated_plan)
        # Check the service was started
        service = self.harness.model.unit.get_container("wireguard").get_service("wireguard")
        self.assertTrue(service.is_running())
        # Ensure we set an ActiveStatus with no message
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
