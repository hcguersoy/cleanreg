#Image as build-environment
FROM python:2.7

RUN apt-get install -y curl

#Download the Dockerclient, because the tests need docker. The docker socket will be mounted in the testrunner-container later
RUN mkdir /setup \
 && cd /setup \
 && curl https://get.docker.com/builds/Linux/i386/docker-latest.tgz -o /setup/docker.tgz \
 && tar -xvzf /setup/docker.tgz \
 && mv /setup/docker/docker /usr/bin/docker

RUN pip install requests PyYAML

ENTRYPOINT ["/bin/bash", "-c"]
