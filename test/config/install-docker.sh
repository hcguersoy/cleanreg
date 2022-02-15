#!/bin/bash

set -e
set -x

linux_arch=$( arch)
echo "Arcghitecture is ${linux_arch}"
case "$linux_arch" in
  aarch64|arm64)
    package_arch=arm64
  ;;
  x86_64)
    package_arch=x86_64
  ;;
  *)
    echo "Unsupported architecture."
    exit 1
esac
curl https://download.docker.com/linux/debian/dists/bullseye/pool/stable/${package_arch}/docker-ce-cli_${DOCKER_PACKAGE_VERSION}~debian-bullseye_arm64.deb -o /tmp/docker-cli.deb
dpkg -i /tmp/docker-cli.deb