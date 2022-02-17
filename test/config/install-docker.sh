#!/bin/bash

set -e
set -x

linux_arch=$( arch)
echo "Architecture is ${linux_arch}"
case "$linux_arch" in
  aarch64|arm64)
    package_arch=arm64
  ;;
  x86_64|amd64)
    package_arch=amd64
  ;;
  *)
    echo "Unsupported architecture."
    exit 1
esac
curl https://download.docker.com/linux/debian/dists/bullseye/pool/stable/${package_arch}/docker-ce-cli_${DOCKER_PACKAGE_VERSION}~debian-bullseye_${package_arch}.deb -o /tmp/docker-cli.deb
dpkg -i /tmp/docker-cli.deb