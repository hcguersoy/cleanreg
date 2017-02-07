# Registry Cleaner

This is a small tool to delete tags, or, to be more correct, delete image manifests, from a Docker Registry implementing the API v2.

Please be aware of that this is a soft delete. You've to run the registry garbage collection after this tool has been applied.

For Docker Registry v2 API specification see [https://docs.docker.com/registry/spec/api/](https://docs.docker.com/registry/spec/api/).

Information about the needed garbage collection is described at [https://docs.docker.com/registry/garbage-collection/](https://docs.docker.com/registry/garbage-collection/).

## History

* v0.2 - added support for registry server using self signed certificates
* v0.1 - first version with basics 

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
                   [-k KEEPIMAGES] [-f REPOSFILE] [-c CACERT]

Removes images on a docker registry (v2).

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         The verbosity level.
  -r REGISTRY, --registry REGISTRY
                        The registry server to connect to, e.g.
                        http://1.2.3.4:5000
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
  -c CACERT, --cacert CACERT
                        Path to a valid CA certificate file. This is needed if
                        self signed TLS is used in the registry server.
```

You can use it directly with the public docker image:

```
docker run --rm -it hcguersoy/cleanreg
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


If you've to use a repositories definition file (parameter `-f`) while using the image distribution you should mount that file into your container:

```
docker run --rm -it -v $(pwd)/cleanreg-example.conf:/cleanreg-example.conf hcguersoy/cleanreg:<version> -r  http://192.168.56.2:5000 -f cleanreg-example.conf
```

There is a simple script added to create multiple image tags (based on `busybox`) on your registry server.

If you have installed a *semi secure* registry server using TLS and self signed certificates you have to provide the path to the CA certificate file:

```
./cleanreg.py -r https://192.168.56.3:5000 -c /my/certifacates/ca.pem -f cleanreg-example.conf
```

If you run *cleanreg* in a container you should not forget to mount the certificate file into the container like configuration file above.

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

Please feel free to contribute your changes as a PR.
