# wireguard-sidecar

## Introduction

Install and run a juju charmed Wireguard server container in Kubernetes.

## Developing

Pebble charms require Juju 2.9.

### Bootstrap MicroK8s

    juju bootstrap microk8s micro
    juju add-model development

### Download and initialize your Sidecar charm:

    sudo snap install charmcraft --beta
    mkdir wireguard-sidecar && cd wireguard-widecar/
    charmcraft init

### Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests

## Running

Ensure your k8s environment is up (I'm using MicroK8s) and connected as a model to your juju controller.

I'm using cmulk's [wireguard docker image](https://hub.docker.com/r/cmulk/wireguard-docker) as the OCI base image resource.

e.g.

    charmcraft build
    juju deploy ./wireguard-sidecar.charm --resource wireguard-image=cmulk/wireguard-docker:alpine --config config_file_b64="$(cat server_wg0.conf | base64)"

As Wireguard requires escalated privileges, you'll need to run `juju trust wireguard-sidecar --scope=cluster` one time.

To connect, get the Wireguard Unit address from `juju status` and enter it with the selected port to your wireguard peer.

    juju status
    ...
    Unit                  Workload  Agent  Address       Ports      Message
    wireguard-sidecar/0*  active    idle   10.1.180.182  52711/UDP
    ...

    sudo vi /etc/wireguard/wg0.conf
    ...
    Endpoint = 10.1.180.182:52711
    ...

    wg-quick up wg0

### Verifying Operations

Just run a `wg show wg0` and verify "latest handshake" and "transfer" rows:

    interface: wg0
      public key: <redacted>
      private key: (hidden)
      listening port: 54166

    peer: <redacted>
      preshared key: (hidden)
      endpoint: 10.1.180.180:52711
      allowed ips: 10.0.0.2/32, 192.168.178.0/24
      latest handshake: 2 minutes, 59 seconds ago
      transfer: 284 B received, 7.71 KiB sent

## Charm Hub & Discourse

Feel free to read more about the [wireguard-sidecar charm](https://charmhub.io/wireguard-sidecar) at charmhub.io.
