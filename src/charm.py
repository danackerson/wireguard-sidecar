#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

import base64
import logging

import kubernetes
from kubernetes.client.rest import ApiException
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, ModelError
from ops.pebble import APIError, ConnectionError

logger = logging.getLogger(__name__)
SERVICE = "wireguard"


class WireguardSidecarCharm(CharmBase):
    _authed = False

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.wireguard_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_pebble_ready(self, event):
        try:
            container = event.workload
            if not container.get_service("wireguard").is_running():
                logger.info("Starting wireguard")
                container.start("wireguard")
        except ModelError as error:
            logger.debug(f"The Pebble API is not ready yet. Error message: {error}")
            event.defer()

    def _check_patched(self) -> bool:
        self.k8s_auth()
        # Get an API client
        cl = kubernetes.client.ApiClient()
        apps_api = kubernetes.client.AppsV1Api(cl)
        statefulset = apps_api.read_namespaced_stateful_set(
            name=self.app.name, namespace=self.model.name)

        app_container = statefulset.spec.template.spec.containers[1]
        patched = \
            app_container.ports is not None and \
            app_container.ports[0].container_port == self.model.config["server_port"] and \
            app_container.ports[0].protocol == "UDP" and \
            app_container.security_context.privileged

        return patched

    def _on_config_changed(self, event) -> None:
        if not self._check_patched():
            self._escalate_wireguard_stateful_set()
            self.unit.status = MaintenanceStatus("waiting for changes to apply")

        container = self.unit.get_container(SERVICE)
        try:
            plan = container.get_plan().to_dict()
        except (APIError, ConnectionError) as error:
            logger.debug(f"The Pebble API is not ready yet. Error message: {error}")
            event.defer()
            return

        layer = self._wireguard_layer()
        plan = container.get_plan()
        if plan.services != layer["services"]:
            container.add_layer("wireguard", layer, combine=True)

            wireguardConfigB64 = self.model.config["config_file_b64"]
            decodedBytes = base64.b64decode(wireguardConfigB64)
            wireguardConfig = str(decodedBytes, "utf-8")
            container.push("/etc/wireguard/wg0.conf", wireguardConfig, make_dirs=True)

            if container.get_service(SERVICE).is_running():
                container.stop(SERVICE)

            container.start(SERVICE)
            logger.info("Restarted wireguard container")

        self.app.status = ActiveStatus()
        self.unit.status = ActiveStatus()

    def _wireguard_layer(self) -> dict:
        return {
            "summary": "wireguard layer",
            "description": "pebble config layer for wireguard",
            "services": {
                "wireguard": {
                    "override": "replace",
                    "summary": "wireguard",
                    "command": "/scripts/run",
                    "startup": "enabled",
                    "environment": {
                        "server_port": self.model.config["server_port"]
                    },
                }
            },
        }

    def _escalate_wireguard_stateful_set(self) -> None:
        """Escalate the statefulset created by Juju to allow for priv access"""
        self.unit.status = MaintenanceStatus("escalating statefulset privileges")

        # https://www.programcreek.com/python/example/123275/kubernetes.client.V1Statefulset
        # https://github.com/jnsgruk/charm-kubernetes-dashboard/blob/master/src/charm.py
        cl = kubernetes.client.ApiClient()
        apps_api = kubernetes.client.AppsV1Api(cl)

        statefulset = apps_api.read_namespaced_stateful_set(
            name=self.app.name, namespace=self.model.name)
        app_container = statefulset.spec.template.spec.containers[1]

        app_container.security_context.privileged = True
        app_container.ports = \
            [kubernetes.client.V1ContainerPort(
             protocol="UDP", container_port=int(self.model.config["server_port"]))]
        logger.info(app_container.env)

        api_response = apps_api.patch_namespaced_stateful_set(
            name=self.app.name, namespace=self.model.name, body=statefulset)
        logger.info("Patched statefulset response = %s" % str(api_response.status))

    def k8s_auth(self):
        """Authenticate to kubernetes."""
        if self._authed:
            return True

        # Authenticate against the Kubernetes API using a mounted ServiceAccount token
        kubernetes.config.load_incluster_config()
        # Test the service account we've got for sufficient perms
        auth_api = kubernetes.client.RbacAuthorizationV1Api(kubernetes.client.ApiClient())
        try:
            auth_api.read_namespaced_role(namespace=self.model.name, name=self.app.name)
        except ApiException:
            # If we can't read a namespaced role, we definitely don't have enough permissions
            self.unit.status = BlockedStatus("Run juju trust on this application to continue")
            return False

        self._authed = True
        return True


if __name__ == "__main__":
    main(WireguardSidecarCharm)
