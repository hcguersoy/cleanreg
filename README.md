# Registry Cleaner 

This is a small tool to delete tags, or, to be more correct, delete image manifests, from a Docker Registry implementing the API v2.

Please be aware of that this is a soft delete. You've to run the registry garbage collection after this tool has been applied.

For Docker Registry v2 API specification see [https://docs.docker.com/registry/spec/api/](https://docs.docker.com/registry/spec/api/).

Information about the needed garbage collection is described at [https://docs.docker.com/registry/garbage-collection/](https://docs.docker.com/registry/garbage-collection/).

## Prerequisits and supported Plattform

This tool was implemented and tested on Ubuntu Linux 14.04, 16.04 and on MacOS 10.12 using Python 2.7. The latest used Docker Resgistry was version [2.5.1](https://github.com/docker/distribution/releases/tag/v2.5.1).

You need to install the Python module *requests*:

```
$ pip install requests
```

Be sure to configure your registry server to allow deletion (see [https://docs.docker.com/registry/configuration/#/delete](https://docs.docker.com/registry/configuration/#/delete)).

## Usage

Download the file *cleanreg.py* or clone this repsitory to a local directory.

```
$ ./cleanreg.py -h
usage: cleanreg.py [-h] [-v] -r REGISTRY [-p] [-q] [-n REPONAME]
                   [-k KEEPIMAGES] [-f REPOSFILE]

Removes images on a docker registry (v2).

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         The verbosity level.
  -r REGISTRY, --registry REGISTRY
                        The registry server to connect to, e.g. 1.2.3.4:5000
  -p, --proxy           Use system level proxy settings accessing registry
                        server if set.By default, the registry server will be
                        accessed without a proxy.
  -q, --quiet           If set no user action will appear and all questions
                        will be answered with YES
  -n REPONAME, --reponame REPONAME
                        The name of the repo which should be cleaned up
  -k KEEPIMAGES, --keepimages KEEPIMAGES
                        Amount of images which should be kept for the given
                        repo.
  -f REPOSFILE, --reposfile REPOSFILE
                        A file containing the list of Repositories and how
                        many images should be kept.
```

## Examples

Cleaning up a single repository called mysql on registry server 192.168.56.2:5000 and keeping 5 of the latest images:

```
./cleanreg.py -r http://192.168.56.2:5000 -n mysql -k 5
```
Cleaning up multiple repositories defined in a configuration file:

```
./cleanreg.py -r http://192.168.56.2:5000 -f cleanreg-example.conf
```
The configuration file has the format `<repository name> <images to keep>`. An example file can be found in the repository.

There is a simple script added to create multiple image tags (based on `busybox`) on your registry server.

## Runing Garbage Collection 

Example on running the garbage collection:

```
$ docker run -it --rm \
  -v /docker/registry2:/var/lib/registry:rw \
  registry:latest bin/registry \ 
  garbage-collect /etc/docker/registry/config.yml
```

This maps the local directory /docker/registry2 into the container, and calls the garbage collection.
The pointed config file is the default configuration.
The registry itself should be stopped before running this.

## Contribution

Please feel free to contribute your chages as a PR.
