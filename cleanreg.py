#!/usr/bin/env python
# coding=utf-8

import sys
import os
import requests
import argparse
from urlparse import urlparse
import json
import collections
from requests.auth import HTTPBasicAuth

__author__ = 'Halil-Cem Guersoy <hcguersoy@gmail.com>, Kevin Krummenauer <kevin@whiledo.de>'
__license__ = '''
------------------------------------------------------------------------------
Copyright 2017
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
 http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
------------------------------------------------------------------------------
'''


def parse_arguments():
    parser = argparse.ArgumentParser(description='Removes images on a docker registry (v2).',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='The verbosity level.')
    parser.add_argument('-r', '--registry', help="The registry server to connect to, e.g. http://1.2.3.4:5000", required=True)
    parser.add_argument('-p', '--proxy', help="Use system level proxy settings accessing registry server if set. "
                                              "By default, the registry server will be accessed without a "
                                              " proxy.", default=False, action='store_true')
    parser.add_argument('-y', '--yes', '--assume-yes', help="If set no user action will appear and all questions will "
                                              "be answered with YES", default=False, action='store_true', dest="assumeyes")
    parser.add_argument('-n', '--reponame', help="The name of the repo which should be cleaned up")
    parser.add_argument('-k', '--keepimages', help="Amount of images (not tags!) which should be kept "
                                                   "for the given repo.",
                        type=int)
    parser.add_argument('-f', '--reposfile', help="A file containing the list of Repositories and "
                                                  "how many images should be kept.")
    parser.add_argument('-c', '--cacert', help="Path to a valid CA certificate file. This is needed if self signed "
                                               "TLS is used in the registry server.", default=None)
    parser.add_argument('-i', '--ignore-ref-tags', help="Ignore a digest, if it is referenced by multiple tags. "
                                                        "ATTENTION: the default if False!",
                        default=False, action='store_true', dest='ignoretag')
    parser.add_argument('-u', '--basicauth-user', help="The username, if the registry is protected with basic auth", dest='basicauthuser')
    parser.add_argument('-pw', '--basicauth-pw', help="The password, if the registry is protected with basic auth", dest='basicauthpw')

    args = parser.parse_args()

    # check if keepimages is set that it is not negative
    if (args.keepimages is not None) and (args.keepimages < 0):
        parser.error("[-k] has to be a positive integer!")

    # hackish mutually exclusive group
    if (args.reponame or (args.keepimages is not None)) and args.reposfile:
        parser.error("[-n|-k] and [-f] cant be used together")

    # hackish dependent arguments
    if bool(args.reponame) ^ (args.keepimages is not None):
        parser.error("[-n] and [-k] has to be used together.")

    # hackish dependent arguments
    if bool(args.reponame or (args.keepimages is not None)) is False and bool(args.reposfile) is False:
        parser.error("[-n|-k] or [-f] has to be used!")
    return args


def update_progress(current, maximum, factor=2):
    if maximum is 0:
        raise Exception('Maximum ammount should not be zero.')
    progress = (100 * current) / maximum
    sys.stdout.write('\r{0}>> {1}%'.format('=' * (progress / factor), progress))
    sys.stdout.flush()


def query_yes_no(question, default="no"):
    """
    Shameless copied from recipe 577058 - http://code.activestate.com/recipes/577058/

    Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def print_headers(headers):
    for header_element in headers:
        print "  > {0}   ->  {1}".format(header_element, headers.get(header_element))


def is_v2_registry(verbose, regserver, cacert=None):
    """
    Checks if the given server is really a v2 registry.
    :param verbose: verbosity level
    :param regserver: the URL of the reg server
    :param cacert: the path to a cacert file
    :return: True if it is really a v2 server
    """

    if verbose > 0:
        print 'Check if registry server supports v2...'
    check_url = regserver
    
    check_result = requests.get(check_url, verify=cacert, auth=get_auth())

    if verbose > 1:
        print "Check result code:", check_result.status_code
        print "Headers"
        print_headers(check_result.headers)

    # check if result header contains API version
    if 'Docker-Distribution-Api-Version' in check_result.headers and \
       check_result.headers['Docker-Distribution-Api-Version'] == 'registry/2.0':
        has_api_v2 = True
    else:
        has_api_v2 = False

    if check_result.status_code == requests.codes.ok and has_api_v2:
        if verbose > 0:
            print "Registry server supports v2!"
        return True
    elif check_result.status_code == requests.codes.ok and has_api_v2 is False:
        print "This is really strange... someone fakes you?"
        return False
    elif check_result.status_code != requests.codes.ok and has_api_v2 is False:
        print "This is not a v2 registry server: ", regserver
        return False
    elif check_result.status_code != requests.codes.ok and has_api_v2:
        print "Found a v2 repo but return code is ", check_result.status_code
        return False

def generate_request_headers(api_version=2):
    if api_version == 1:
        accept_string = 'application/vnd.docker.distribution.manifest.v1+json'
    else:
        accept_string = 'application/vnd.docker.distribution.manifest.v2+json'
    headers = {'Accept': accept_string}
    return headers

def get_auth():
    if (args.basicauthuser is not None) and (args.basicauthpw is not None):
        return HTTPBasicAuth(args.basicauthuser, args.basicauthpw)
    else:
        return None    

def get_digest_by_tag(verbose, regserver, repository, tag, cacert=None):
    """
    Retrieves the Digest of an image tag.

    :param verbose: verbosity level
    :param regserver: the URL of the reg server
    :param repository: the repositroy name
    :param tag: the tag of the image
    :param cacert: the path to a cacert file
    :return: The docker image digest
    """
    # set accept type
    req_headers = generate_request_headers()
    req_url = regserver + repository + "/manifests/" + tag
    if verbose > 1:
        print "Will use following URL to retrieve digest:", req_url
    head_result = requests.head(req_url, headers=req_headers, verify=cacert, auth=get_auth())

    head_status = head_result.status_code
    if verbose > 2:
        print "Digest head result status code is:", head_status
        print "Digest head header is:"
        print_headers(head_result.headers)

    # check the return code and exit if not OK
    if head_status != requests.codes.ok:
        print "The digest could not be retrieved due to error:", head_status
        if verbose > 0:
            print head_result
        sys.exit(2)
    # if the header doesn't contains the digest information exit, too
    if 'Docker-Content-Digest' not in head_result.headers:
        print "Could not find any digest information in the header. Exiting"
        sys.exit(3)
    # everything looks fine so we continue
    cur_digest = head_result.headers['Docker-Content-Digest']

    if verbose > 0:
        print "Digest for image {0}:{1} is [{2}]".format(repository, tag, cur_digest)

    return cur_digest


def delete_manifest(verbose, regserver, repository, cur_digest, cacert=None):
    """
    Deletes a manifest based on a digest.
    Be aware that a digest can be associated with multiple tags!

    :param verbose: verbosity level
    :param regserver: the URL of the reg server
    :param repository: the repositroy name
    :param cur_digest: the digest if the image which has to be deleted
    :param cacert: the path to a cacert file
    """
    # Attention: this is needed if you are running a registry >= 2.3
    req_headers = generate_request_headers()
    req_url = regserver + repository + "/manifests/" + cur_digest
    # as specified by the v2 API, DELETE returns a 202
    # Be aware of the real intention of this status code:
    # "The request has been accepted for processing, but the processing has not been completed."
    # s. https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
    del_status_ok = 202
    if verbose > 1:
        print "Will use following URL to delete manifest:", req_url
    delete_result = requests.delete(req_url, headers=req_headers, verify=cacert, auth=get_auth())
    delete_status = delete_result.status_code
    if verbose > 1:
        print "Delete result status code is:", delete_status
    if verbose > 2:
        print "Delete result header is:"
        print_headers(delete_result.headers)

    if delete_status != del_status_ok:
        print "The manifest could not be deleted due to an error:", delete_status
        if verbose > 1:
            print delete_result
        sys.exit(12)

    if verbose > 0:
        print "Deleted manifest with digest", cur_digest


def deletion_digests(verbose, regserver, repository, delete_tags, ignore, cacert):
    """
    High level method to delete tags from a repositroy.

    :param verbose: verbosity level
    :param regserver: the URL of the reg server
    :param repository: the repository name
    :param delete_tags: the tags which has to be deleted
    :param ignore: ignore tags if their digests are referenced multiple times
    :param cacert: the path to a cacert file
    """

    deletion_digests = []
    all_digests = []

    for currenttag, _ in delete_tags:
        digest = get_digest_by_tag(verbose, regserver, repository, currenttag, cacert)
        if verbose > 1:
            print "Found digest {0} for tag {1}".format(digest, currenttag)
        all_digests.append(digest)

    diggests_occurences = collections.Counter(all_digests)
    digests_counts = diggests_occurences.items()

    for dig, count in digests_counts:
        if verbose > 1:
            print "Digest: {0}, count: {1}".format(dig, count)

        if ignore is True and count > 1:
            print "Ignoring digest {0} as it is referenced multiple times!".format(dig)
        else:
            deletion_digests.append(dig)

    if verbose > 1:
        print "Digests to be deleted:", deletion_digests

    return deletion_digests


def create_repo_list(cmd_args):
    """
    Builds up a dict of repositories which have to be cleaned up and how many
    images have to be kept.

    :param cmd_args: the command line arguments
    :return: A dict in the format repositoryname : amount of images to be kept
             and a list of the repository names
    """
    if bool(cmd_args.reponame) and (cmd_args.keepimages is not None):
        if cmd_args.verbose > 1:
            print "In single repo mode."
            print "Will keep {0} images from repo {1}".format(cmd_args.keepimages, cmd_args.reponame)
        found_repos_counts = {cmd_args.reponame: cmd_args.keepimages}
        if cmd_args.verbose > 2:
            print "repos_counts: ", found_repos_counts
    else:
        if cmd_args.verbose > 1:
            print "Will read repo information from file {0}".format(cmd_args.reposfile)
        found_repos_counts = {}
        with open(cmd_args.reposfile) as repoFile:
            for line in repoFile:
                if cmd_args.verbose > 2:
                    print "Import line ", line
                (reponame, keep) = line.split()
                found_repos_counts[reponame] = int(keep)
    if cmd_args.verbose > 1:
        print "These repos will be processed:"
        print found_repos_counts

    return found_repos_counts, found_repos_counts.keys()


def get_deletiontags(cmd_args, reg_server, reponame, repo_count, cacert=None):
    """
    Returns a dict containing a list of the tags which could be deleted due
    to name and date.

    :param cmd_args: the command line arguments
    :param reg_server: regserver: the URL of the reg server
    :param reponame: the repository name
    :param repo_count: amount of tags to be kept in repository
    :param cacert: the path to a cacert file
    :return: a dict of tags to be deleted and the date then they are created
    """
    deletion_tags = {}
    req_url = reg_server + reponame + "/tags/list"
    if cmd_args.verbose > 1:
        print "Will use following URL to retirve tags:", req_url
    tags_result = requests.get(req_url, verify=cacert, auth=get_auth())
    tags_status = tags_result.status_code
    if args.verbose > 2:
        print "Get tags result is:", tags_status
    # check the return code and exit if not OK
    if tags_status != requests.codes.ok:
        print "The tags could not be retrieved due to error:", tags_status
        if args.verbose > 0:
            print tags_result
        sys.exit(2)
    tags_result_json = tags_result.json()

    tags_all = tags_result_json['tags']
    if cmd_args.verbose > 1:
        print "Found tags for repo {0}: {1} ".format(reponame, tags_all)
    tag_dates = {}
    if tags_all is None:
        ammount_tags = 0
    else:
        ammount_tags = len(tags_all)
    if cmd_args.verbose > 2:
        print "ammount_tags : ", ammount_tags
        print "repo_count : ", repo_count
    if ammount_tags > repo_count:
        if cmd_args.verbose > 0:
            print "Retrieving metada for repository ", reponame
        for key in tags_all:
            metadata_request = reg_server + reponame + "//manifests/" + key
            metadata_header = {'Accept': 'application/vnd.docker.distribution.manifest.v1+json'}
            metadata = requests.get(metadata_request, headers=metadata_header, verify=cacert, auth=get_auth()).json()
            # pick the latest history entry and grab the creation date of the image
            # be aware that is NOT the tagging date but image creation!
            tag_dates[key] = json.loads(metadata['history'][0]['v1Compatibility'])['created']
        sorted_tags = sorted(tag_dates.iteritems(), key=lambda (k, v): (v, k), reverse=True)
        deletion_tags = sorted_tags[repo_count:]
        if cmd_args.verbose > 2:
            print
            for tag_tag, tag_date in deletion_tags:
                print "Tag {0} created on {1} ".format(tag_tag, tag_date)
    else:
        if cmd_args.verbose > 0:
            print "Skipping because not found images which can be deleted."
    return deletion_tags

# >>>>>>>>>>>>>>>> MAIN STUFF

args = parse_arguments()

reg_server_api = args.registry + "/v2/"

if args.proxy is False:
    if args.verbose > 1:
        print "Will exclude registryserver location from proxy:", urlparse(args.registry).netloc
    os.environ['no_proxy'] = urlparse(args.registry).netloc

# initially check if we've a v2 registry server
if is_v2_registry(args.verbose, reg_server_api, args.cacert) is False:
    print "Exiting, none V2 registry."
    sys.exit(1)

repos_counts, repos = create_repo_list(args)

x = 0
repo_del_tags = {}
repo_del_digests = {}
for repo, count in repos_counts.iteritems():
    x += 1
    update_progress(x, len(repos_counts))
    if args.verbose > 0:
        print
        print "will delete repo {0} and keep {1} images.".format(repo, count)
    del_tags = get_deletiontags(args, reg_server_api, repo, count, args.cacert)
    if len(del_tags) > 0:
        repo_del_tags[repo] = del_tags
        repo_del_digests[repo] = deletion_digests(args.verbose, reg_server_api, repo, del_tags, args.ignoretag,
                                                  args.cacert)

answer = True
if args.assumeyes is False and len(repo_del_digests) > 0:
    print
    print "Repos and according digests to be deleted:"
    for repo, del_digests in repo_del_digests.iteritems():
        print "Repository: ", repo
        for digest in del_digests:
            print "     {0}".format(digest)
    answer = query_yes_no("Do you realy want to delete them?")

if answer is True and len(repo_del_digests) > 0:
    print "Deleting!"
    for repo, del_digests in repo_del_digests.iteritems():
        for digest in del_digests:
            # delete_tag(args.verbose, reg_server_api, repo, tag, args.cacert)
            print "Deleting ", digest
            delete_manifest(args.verbose, reg_server_api, repo, digest, args.cacert)
else:
    print "Aborted by user or nothing to delete."
    sys.exit(1)

print
print "Finished"
sys.exit(0)
