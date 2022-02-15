
# Registry Cleaner

This is a small tool to delete tags, or, to be more correct, delete image manifests, from a Docker Registry implementing the API v2.

Please be aware of that this is a soft delete. You've to run the registry garbage collection after this tool has been applied.

Information about the needed garbage collection is described at [https://docs.docker.com/registry/garbage-collection/](https://docs.docker.com/registry/garbage-collection/).

## History

* v0.8 - Migration to Python 3 and Github Actions
* v0.7.1 - Added a `--skip-tls-verify` attribute (_unreleased_)
* v0.7 - This is a release which breaks some stuff (configuration file is now yaml based), adding new options for keeping images (e.g. `--since`, `--regex`) (thanks to @JulianSauer for his [PR10](https://github.com/hcguersoy/cleanreg/pull/10))
* v0.6 - add `-cf` flag which allows to clean up all repos in a registry (thanks @kekru for his PR)
* v0.5 - fix for issue [#8](https://github.com/hcguersoy/cleanreg/issues/8) which resulted in deleting more layers then intended; performance improvements; added `--metadata-workers` attribute
* v0.4.1 - added `--assume-yes` and deprecated `--quiet` flag
* v0.4 - added support for basic auth secured registry servers, introducing `--basicauth-user` and `--basicauth-pw` (thanks to @kekru for his pull request)
* v0.3 - fixing deletion if a digest is associated with multiple tags, introducing the `--ignore-ref-tags` flag.
* v0.2 - added support for registry server using self signed certificates
* v0.1 - first version with basics

## Prerequisites and supported Plattform

You need Docker and a Docker registry system which implements the Registry API v2.
For Docker Registry v2 API specification see [https://docs.docker.com/registry/spec/api/](https://docs.docker.com/registry/spec/api/).

Be sure to configure your registry server to allow deletion (see [https://docs.docker.com/registry/configuration/#/delete](https://docs.docker.com/registry/configuration/#/delete)).

## Usage

Download the file *cleanreg.py* or clone this repository to a local directory or pull the docker image. This is the suggested way to run `cleanreg`!

```shell
docker pull hcguersoy/cleanreg:v0.8.0
```

The image is hosted here: [https://hub.docker.com/r/hcguersoy/cleanreg/](https://hub.docker.com/r/hcguersoy/cleanreg/ "")

_Hint:_ `latest` tag is not supported (you know, `latest` is evil :imp:).

To get a immediate help simply run it without any parameters:

```shell
$ docker run --rm hcguersoy/cleanreg:v0.8.0
usage: cleanreg.py [-h] [-v] -r REGISTRY [-p] [-y] [-q] [-n REPONAME:TAG]
                   [-k KEEPIMAGES] [-re] [-d DATE]
                   [-f REPOSFILE] [-c CACERT] [-sv] [-i] [-u BASICAUTHUSER]
                   [-pw BASICAUTHPW] [-w MD_WORKERS]

Removes images on a docker registry (v2).

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         The verbosity level. Increase verbosity by multiple
                        usage, e.g. -vvv .
  -r REGISTRY, --registry REGISTRY
                        The registry server to connect to, e.g.
                        http://1.2.3.4:5000
  -p, --proxy           Use system level proxy settings accessing registry
                        server if set. By default, the registry server will be
                        accessed without a proxy.
  -y, --yes, --assume-yes
                        If set no user action will appear and all questions
                        will be answered with YES
  -q, --quiet           [deprecated] If set no user action will appear and all
                        questions will be answered with YES
  -n REPONAME, --reponame REPONAME:TAG
                        The name of the repo which should be cleaned up. Tags
                        are optional.
  -cf, --clean-full-catalog
                        If set all repos of the registry will be cleaned up,
                        considering the -k, -re and -d options.
                        These can be overridden for each repo in the repofile (-f).
  -k KEEPIMAGES, --keepimages KEEPIMAGES
                        Amount of images (not tags!) which should be kept for
                        the given repo  (if -n is set) or for each repo of the
                        registry (if -cf is set).
  -re, --regex
                        Interpret tagnames as regular expressions for the given
                        repo  (if -n is set) or for each repo of the registry (if
                        -cf is set).
  -s DATE, --since DATE
                        Keeps images which were created since then for
                        the given repo  (if -n is set) or for each repo of the
                        registry (if -cf is set).
                        Format: YYYYMMDD, YYYYMMDDThhmmss, YYYY-MM-DD or YYYY-MM-DDThh:mm:ss
  -f REPOSFILE, --reposfile REPOSFILE
                        A yaml file containing the list of Repositories with
                        additional information regarding tags, dates and how many
                        images to keep.
                        Format: REPONAME:
                            tag: TAG
                            keepimages: KEEPIMAGES
                            keepsince: DATE
  -c CACERT, --cacert CACERT
                        Path to a valid CA certificate file. This is needed if
                        self signed TLS is used in the registry server.
  -sv, --skip-tls-verify
                        If set insecure TLS is allowed, so no need for
                        a valid cert to verify.
  -i, --ignore-ref-tags
                        Ignore a digest if it is referenced multiple times in
                        the whole registry server. In this case, a list of all
                        repositories and their images will be retrieved which
                        can be time and memory consuming. ATTENTION: the
                        default is False so an image will be deleted even it
                        is referenced multiple times.
  -u BASICAUTHUSER, --basicauth-user BASICAUTHUSER
                        The username, if the registry is protected with basic
                        auth
  -pw BASICAUTHPW, --basicauth-pw BASICAUTHPW
                        The password, if the registry is protected with basic
                        auth
  -w MD_WORKERS, --metadata-workers MD_WORKERS
                        Parallel workers to retrieve image metadata. Default
                        value is 6.

```

If you've to use a configuration file (parameter `-f`) you should mount that file into your container:

```shell
docker run --rm -it -v $(pwd)/cleanreg-example.conf:/cleanreg-example.yaml hcguersoy/cleanreg:<version> -r  http://192.168.56.2:5000 -f cleanreg-example.yaml -i
```

As an alternative, you can create your own image, inheriting from `cleanreg`:

```shell
FROM hcguersoy/cleanreg:<version>
ADD myconfig.yaml /config.yaml
```

## Examples

**Attention:** It is strongly recommended that you use the _-i_ flag even it is more time and memory consuming. If not you can delete images / layers which you not wanted to delete because registry itself doesn't check if a digest is referenced by multiple tags!

Cleaning up a single repository called mysql on registry server 192.168.56.2:5000 and keeping 5 of the latest images:

```shell
docker run --rm -it hcguersoy/cleanreg:<version> -r http://192.168.56.2:5000 -n mysql -k 5
```

Be aware that you don't keep here the five last tags but digests/images. As a digest can be associated with multiple tags this can result in deletion of images which you not intended in!
Again: to be secure use the `-i` flag:

```shell
docker run --rm -it hcguersoy/cleanreg:<version> -r http://192.168.56.2:5000 -n mysql -k 5 -i
```

Same as above but ignore images which are associated with multiple tags.

```shell
docker run --rm -it hcguersoy/cleanreg:<version> -r http://192.168.56.2:5000 -n mysql:latest -i
```

Will only delete the image mysql which is tagged as latest.

```shell
docker run --rm -it hcguersoy/cleanreg:<version> -r http://192.168.56.2:5000 -n mysql:.*temp.* -re -d 2018-01-01 -k 5 -i
```

Removes all images that contain the word "temp" in their tagnames and if they were created before 2018 but at least 5 will be kept in total.

```shell
docker run --rm -it hcguersoy/cleanreg:<version> -r http://192.168.56.2:5000 -n myalpine -k 50 -i -w 12
```

If you have a very large registry and enough bandwidth you can increase the parallel workers to retrieve the image metadata. The default is _6_. Be aware that you can generate a _DoS_ on your registry server by increasing to much.

Cleaning up all repositories of the registry:

```shell
docker run --rm -it hcguersoy/cleanreg:<version> -r http://192.168.56.2:5000 -cf -k 5 -i
```

This will clean up all repositories, keeping 5 images per repository.

Cleaning up multiple repositories defined in a configuration file:

```shell
docker run --rm -it \
        -v $(pwd)/cleanreg-example.conf:/cleanreg-example.yaml \
       hcguersoy/cleanreg:<version>  \
       -r http://192.168.56.2:5000 \
       -f /cleanreg-example.yaml \
       -re \
       -i
```

The configuration file has the format

```yaml
<repository name>:
    tag: <tag>
    keepimages: <number of images to keep>
    keepsince: <date>
```

The values for `tag`, `keepimages` and `keepsince` are optional. If the tag should be parsed as a regular expression use the `-re` flag as shown above. A simple example for the configuration file:

```yaml
consul:
  tag: OnlyThisTag
  keepimages: 20
  keepsince: 2000-12-24T12:31:59
elasticsearch:
  keepimages: 20
  keepsince: 20000101
dummybox:
  keepimages: 0
```

The configuration file can be used together with the clean-full-catalog option:

```shell
./cleanreg.py -r http://192.168.56.2:5000 -cf -d 20180101 -f cleanreg-example.conf -i
```

This will clean the repositories with images to keep as defined in the configuration file and it will additionally clean all other repositories of the registry, keeping images per repository that were created since 2018.

There is a simple script added to create multiple image tags (based on `busybox`) on your registry server.

If you have installed a _semi secure_ registry server using TLS and self signed certificates you have to provide the path to the CA certificate file:

```shell
./cleanreg.py -r https://192.168.56.3:5000 -c /my/certifacates/ca.pem -f cleanreg-example.conf -i
```

If you run _cleanreg_ in a container you should not forget to mount the certificate file into the container like the configuration file above.
Alternatively you can set the option `--skip-tls-verify`. In this case, you don't need to provide a certifictae.

> :exclamation: be aware that this should only used for (local) testing but not for productive environments.

If your registry is protected with basic auth and the username is `test` and the password is `secret`, you have to pass these credentials to _cleanreg_.

```shell
./cleanreg.py -r https://192.168.56.3:5000 -u test -pw secret -f cleanreg-example.conf
```

## Runing Garbage Collection

Example on running the garbage collection:

```shell
$ docker run --rm \
  -v /docker/registry2:/var/lib/registry:rw \
  registry:latest bin/registry \
  garbage-collect /etc/docker/registry/config.yml
```

This maps the local directory /docker/registry2 into the container, and calls the garbage collection.
The pointed config file is the default configuration.
The registry itself should be stopped before running this.

## Contribution

Feel free to contribute your changes as a PR. Please ensure that the tests run without errors and provide tests for additional functionality.

This tool was initially implemented and tested on Ubuntu Linux 16.04 and on MacOS 10.13 using Python 2.7 and migrated to Python 3.10 on macOS 12 (arm64).
It is developed and tested against Docker Registry versions [2.7.1](https://github.com/docker/distribution/releases/tag/v2.7.1)and [2.8.0](https://github.com/docker/distribution/releases/tag/v2.8.8). It should work with older registry versions but they are not tested.

You need to install the Python modules _requests_ and _PyYAML_:

```shell
$ pip install requests PyYAML
```

Be sure to configure your registry server to allow deletion (see [https://docs.docker.com/registry/configuration/#delete](https://docs.docker.com/registry/configuration/#delete)).

### Run tests

Prerequisites:

* Bash
* Locally installed Docker engine. Remote execution is not yet implemented. Runs with [Rancher Desktop](https://rancherdesktop.io) on macOS fine (configured to use _dockerd_ as runtime).

You can run all tests, with the _runAllTests.sh_ script:

```shell
cd test
./runAllTests.sh
```

This will run all tests and repeat them for different versions of the Docker Registry.

To run a single test, change to the `test/tests` directory and run a test script:

```shell
cd test/tests
./simple_clean.sh
```

By default the test will start the Docker Registry from Docker Hub with the tag `latest`.
To specify another registry version, set it using the environment variable `REGISTRYTAG`.

```shell
cd test/tests
export REGISTRYTAG=2.5.1
./simple_clean.sh
```
