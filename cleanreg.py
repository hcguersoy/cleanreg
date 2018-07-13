#!/usr/bin/env python
# coding=utf-8
import sys
import os
import requests
import argparse
from urlparse import urlparse
import re
import json
import collections
from requests.auth import HTTPBasicAuth
from datetime import datetime
from multiprocessing import Manager, Process, Pool, current_process
from itertools import islice
from functools import partial

__author__ = 'Halil-Cem Guersoy <hcguersoy@gmail.com>, ' \
             'Kevin Krummenauer <kevin@whiledo.de>', \
             'Marvin becker <mail@derwebcoder.de>'
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
                        help='The verbosity level. Increase verbosity by multiple usage, e.g. -vvv .')
    parser.add_argument('-r', '--registry', help="The registry server to connect to, e.g. http://1.2.3.4:5000",
                        required=True)
    parser.add_argument('-p', '--proxy', help="Use system level proxy settings accessing registry server if set. "
                                              "By default, the registry server will be accessed without a "
                                              " proxy.", default=False, action='store_true')
    parser.add_argument('-y', '--yes', '--assume-yes', help="If set no user action will appear and all questions "
                                                            "will be answered with YES", default=False,
                        action='store_true', dest="assumeyes")
    parser.add_argument('-q', '--quiet', help="[deprecated] If set no user action will appear and all questions will "
                                              "be answered with YES", default=False, action='store_true')
    parser.add_argument('-n', '--reponame', help="The name of the repo which should be cleaned up")
    parser.add_argument('-cf', '--clean-full-catalog', help="If set all repos of the registry will be cleaned up, "
                                                            "keeping the amount of images specified in -k option. "
                                                            "The amount for each repo can be overridden in the repofile (-f).",
                                                            default=False, action='store_true', dest='clean_full_catalog')
    parser.add_argument('-k', '--keepimages', help="Amount of images (not tags!) which should be kept "
                                                   "for the given repo (if -n is set) or for each repo of the "
                                                   "registry (if -cf is set).", default=0, type=int)
    parser.add_argument('-re', '--regex', help="Use a regular expression as a tagname", default=False,
                        action='store_true', dest="regex")
    parser.add_argument('-d', '--date', help="Keep images which were created since this date. Format: dd.mm.yyyy", default=None)
    parser.add_argument('-f', '--reposfile', help="A file containing the list of Repositories and "
                                                  "how many images should be kept.")
    parser.add_argument('-c', '--cacert', help="Path to a valid CA certificate file. This is needed if self signed "
                                               "TLS is used in the registry server.", default=None)
    parser.add_argument('-i', '--ignore-ref-tags', help="Ignore a digest if it is referenced multiple times "
                                                        "in the whole registry server. In this case, a list of all "
                                                        "repositories and their images will be retrieved which can be "
                                                        "time and memory consuming. "
                                                        "ATTENTION: the default is False so an image will be deleted "
                                                        "even it is referenced multiple times.",
                        default=False, action='store_true', dest='ignoretag')
    parser.add_argument('-u', '--basicauth-user', help="The username, if the registry is protected with basic auth",
                        dest='basicauthuser')
    parser.add_argument('-pw', '--basicauth-pw', help="The password, if the registry is protected with basic auth",
                        dest='basicauthpw')
    parser.add_argument('-w', '--metadata-workers', help="Parallel workers to retrieve image metadata. "
                                                         "Default value is 6.",
                        default=6, type=int, dest='md_workers')

    args = parser.parse_args()

    # check if keepimages is set that it is not negative
    if (args.keepimages is not None) and (args.keepimages < 0):
        parser.error("[-k] has to be a positive integer!")

    # check if date is valid
    if args.date is not None:
        try:
            datetime.strptime(args.date, '%Y%m%d')
        except ValueError:
            try:
                datetime.strptime(args.date, '%Y-%m-%d')
            except ValueError:
                parser.error("[-d] format should be YYYYMMDD")
    
    # hackish mutually exclusive group
    if bool(args.reponame) and bool(args.reposfile):
        parser.error("[-n] and [-f] cant be used together")

    # hackish mutually exclusive group
    if bool(args.reponame) and bool(args.clean_full_catalog):
        parser.error("[-n] and [-cf] cant be used together")

    # hackish dependent arguments
    if (bool(args.reponame) or args.clean_full_catalog) ^ (args.keepimages is not 0 or args.regex is True or args.date is not None):
        parser.error("[-n] or [-cf] have to be used together with [-k], [-re] or [-d].")

    # hackish dependent arguments
    if bool(args.reponame) is False and args.clean_full_catalog is False and bool(args.reposfile) is False:
        parser.error("[-n|-k] or [-cf|-k] or [-f] has to be used!")
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


def deletion_digests(verbose, del_tags, digests_counts, ignore):
    """
    High level method to retrieve digests to be deleted from a repository, based on tags.

    :param verbose: verbosity level
    :param del_tags The tags to be deleted of this repository
    :param digests_counts A dict containing all digest and how often they occur
    :param ignore: ignore tags if their digests are referenced multiple times (occurrence > 1)
    :return The list of digests which have to be deleted
    """

    deletion_digests = []

    for tag, data in del_tags.items():
        if ignore is True and digests_counts[data['digest']] > 1:
            if verbose > 0:
                print "Ignoring digest {0} as it is referenced multiple times!".format(data['digest'])
        else:
            deletion_digests.append(data['digest'])

    return deletion_digests


def get_all_repos(verbose, regserver, cacert=None):
    """
    A method to retrieve a list of all repositories on the registry server.
    :param verbose: verbosity level
    :param regserver:  The registry server
    :param cacert: the path to a cacert file
    :return: A list with all repositories
    """
    req_url = regserver + "_catalog"
    if verbose > 1:
        print "Will use URL {0} to retrieve a list of all repositories:".format(req_url)
    repos_result = requests.get(req_url, verify=cacert, auth=get_auth())
    repos_status = repos_result.status_code
    if args.verbose > 2:
        print "Get catalog result is:", repos_status

    # check the return code and exit if not OK
    if repos_status != requests.codes.ok:
        print "The tags could not be retrieved due to error:", repos_status
        if args.verbose > 0:
            print repos_result
        sys.exit(2)
    repos_result_json = repos_result.json()

    repos_all = repos_result_json['repositories']
    if verbose > 1:
        print "Found repos: {0} ".format(repos_all)

    return repos_all


def create_repo_list(cmd_args, regserver):
    """
    Builds up a dict of repositories which have to be cleaned up and which
    images have to be kept.
    If the ignoreflag is set, a list of all repositories will be retrieved.

    :param regserver: The registry server
    :param cmd_args: the command line arguments
    :return: A dict in the format repositoryname : amount of images to be kept
             and a list of the repository names
    """
    found_repos_counts = {}
    all_registry_repos = get_all_repos(cmd_args.verbose, regserver, cmd_args.cacert)

    if bool(cmd_args.reponame) is True:
        if cmd_args.verbose > 1:
            print "In single repo mode."
            print "Will keep matching images from repo {0}".format(cmd_args.reponame)

        splittedNames = cmd_args.reponame.split(':')
        repo = splittedNames[0]
        tagname = ''
        if len(splittedNames) == 2:
            tagname = splittedNames[1]
        found_repos_counts[repo] = (cmd_args.keepimages, tagname, cmd_args.date)

        if cmd_args.verbose > 2:
            print "repos_counts: ", found_repos_counts
    
    if cmd_args.clean_full_catalog is True:
        if cmd_args.verbose > 1:
            print "Importing all repos of the registries catalog, keeping {0} images per repo.".format(cmd_args.keepimages)
        for repo in all_registry_repos:
            splittedNames = repo.split(':')
            repo = splittedNames[0]
            tagname = ''
            if len(splittedNames) == 2:
                tagname = splittedNames[1]
            found_repos_counts[repo] = (cmd_args.keepimages, tagname, cmd_args.date)
            
    if bool(args.reposfile) is True:
        if cmd_args.verbose > 1:
            print "Will read repo information from file {0}".format(cmd_args.reposfile)
        with open(cmd_args.reposfile) as repoFile:
            for line in repoFile:
                line = line.split('#', 1)[0]
                line = line.strip()
                if line:
                    if cmd_args.verbose > 2:
                        print "Import line ", line
                    (reponame, keep, date) = line.split()
                    splittedNames = reponame.split(':')
                    tagname = ''
                    reponame = splittedNames[0]
                    if len(splittedNames) == 2:
                        tagname = splittedNames[1]
                    if keep != "_":
                        found_repos_counts[reponame] = (int(keep), tagname, date)
                    else:
                        found_repos_counts[reponame] = (0, tagname, date)

    if cmd_args.verbose > 1:
        print "These repos will be processed:"
        print found_repos_counts

    for repo in found_repos_counts.keys():
        if repo not in all_registry_repos:
            del found_repos_counts[repo]
            if cmd_args.verbose > 1:
                print "Skipping repo {0} because it is not in the catalog.".format(repo)

    if cmd_args.ignoretag is True:
        repos = all_registry_repos
    else:
        repos = found_repos_counts.keys()

    return found_repos_counts, repos

def retrieve_metadata(tag, verbose, regserver, repo, managed_tags_date_digests,
                      managed_digests, cacert):

    if verbose > 2:
        print "Processing in", current_process()

    metadata_request = regserver + repo + "//manifests/" + tag
    metadata_header = {'Accept': 'application/vnd.docker.distribution.manifest.v1+json'}
    metadata = requests.get(metadata_request, headers=metadata_header, verify=cacert,
                            auth=get_auth()).json()

    creation_date = json.loads(metadata['history'][0]['v1Compatibility'])['created']
    digest = get_digest_by_tag(verbose, regserver, repo, tag, cacert)
    managed_tags_date_digests[tag] = {'date': creation_date, 'digest': digest}
    managed_digests.append(digest)

    if verbose > 2:
        print "Added {0} to tag {1} on repo {2}".format(managed_tags_date_digests[tag], tag, repo)

    return managed_tags_date_digests, managed_digests


def get_tags_dates_digests_byrepo(verbose, regserver, repo, results, digests, md_workers, cacert=None):
    """
        Retrieves all Tags, the creation date of the layer the tag point to and digest of the layer.
        
    :param verbose: The verbosity level
    :param regserver: The registry server
    :param repo: The repository name
    :param results: A managed dict which is used to return a dict containing the tag, date and digest
    :param digests: A managed list which contains a list of all found digests, used to check for multiple usage
    :param md_workers: Ammount of parallel workers to retrieve metadata
    :param cacert: The path to the certificate file
    :return: Returns using the managed collections results and digests
    """
    manager = Manager()
    managed_tags_date_digests = manager.dict()
    pool = Pool(processes=md_workers)

    req_url = regserver + repo + "/tags/list"
    if verbose > 1:
        print "Will use URL {0} to retrieve tags for repo {1}:".format(req_url, repo)
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
    if verbose > 1:
        print "Found tags for repo {0}: {1} ".format(repo, tags_all)

    if tags_all is None:
        ammount_tags = 0
    else:
        ammount_tags = len(tags_all)
    if verbose > 2:
        print "ammount_tags : ", ammount_tags
    if verbose > 0:
        print "Retrieving metada for repository ", repo

    funcpart = partial(retrieve_metadata, verbose=verbose, regserver=regserver, repo=repo,
                       managed_tags_date_digests=managed_tags_date_digests,
                       managed_digests=digests, cacert=cacert)
    pool.map(funcpart, tags_all)

    # convert managed dict to a "normal dict" and put it into the other managed dict...
    # Feels so unpythonic, should rewrite the stuff
    # TODO make this more pythonic
    tags_date_digests = {}
    for (k, v) in managed_tags_date_digests.items():
        tags_date_digests[k] = v

    results[repo] = tags_date_digests


def get_all_tags_dates_digests(verbose, regserver, repositories, md_workers, cacert=None):
    """
    Retrieve all tags and finally digests for all repositories.
    
    :param verbose: verbosity level
    :param regserver: the URL of the reg server
    :param repositories: the list of repositories to be cleaned up 
    :param cacert: the path to a cacert file
    :return: a nested dict containing all repos and for each repo the list of all tags and their digests. 
    """

    result = {}
    manager = Manager()
    repos_tags_digest = manager.dict()
    managed_digests = manager.list()
    procs = []

    print "Retrieving tags and digests. Be patient, this can take a little bit time."

    for repo in repositories:
        if verbose > 0:
            print "Starting procs for {0}".format(repo)

        # start a process to retrieve the needed data
        proc = Process(target=get_tags_dates_digests_byrepo, args=(verbose, regserver, repo, repos_tags_digest,
                                                                   managed_digests, md_workers, cacert))
        procs.append(proc)
        proc.start()

    for proc in procs:
        if verbose > 1:
            print "Waiting for {0} to be finished.".format(proc)
        proc.join()

    for repo in repositories:
        if verbose > 0:
            print "Retrieving results..."
        result[repo] = repos_tags_digest[repo]

    return result, managed_digests


def get_deletiontags(verbose, tags_dates_digests, repo, tagname, repo_count, regex, date):
    """
    Returns a dict containing a list of the tags which could be deleted due
    to name and date.

    :param tags_dates_digests: A dict containing image tags, their corresponding digest and the layer creation date 
    :param verbose: The verbosity level
    :param repo: the repository name
    :param tagname: tag of the repo
    :param repo_count: amount of tags to be kept in repository
    :param regex: True if tagnames should be interpreted as regular expressions
    :param date: Keeps tags which were created since this date
    :return: a dict of tags to be deleted, their digest and the date then they are created
    """

    all_tags = collections.OrderedDict(sorted(tags_dates_digests.iteritems(), key=lambda x: x[1]['date']))
    deletion_tags = {}

    if verbose > 3:
        print (json.dumps(all_tags, indent=2))
        # for (k, v) in all_tags.iteritems():

    if all_tags is None:
        ammount_tags = 0
    else:
        ammount_tags = len(all_tags)

    if repo_count is None:
        repo_count = 0

    if verbose > 1:
        print "Repo {0}: ammount_tags : {1}; repo_count: {2}".format(repo, ammount_tags, repo_count)

        deletion_tags = all_tags
        if regex and tagname != "":
            deletion_tags = {k: deletion_tags[k] for k in deletion_tags if re.match(tagname, k)}
        elif not regex and tagname != "":
            deletion_tags = {k: deletion_tags[k] for k in deletion_tags if tagname == k}
        if date is not None and date != "_" and date != "":
            try:
                parsed_date = datetime.strptime(date, '%Y%m%d')
            except ValueError:
                parsed_date =  datetime.strptime(date, '%Y-%m-%d')
            for tag in deletion_tags.keys():
                print deletion_tags[tag]['date']
                tag_date = datetime.strptime(deletion_tags[tag]['date'].split('T')[0], '%Y-%m-%d')
                if tag_date >= parsed_date:
                    del deletion_tags[tag]

    if len(deletion_tags) > (ammount_tags - repo_count):
        deletion_tags = collections.OrderedDict(islice(deletion_tags.iteritems(), len(deletion_tags) - (ammount_tags - repo_count)))
        if verbose > 1:
            print
            print "Deletion candidates for repo {0}".format(repo)
            print (json.dumps(deletion_tags, indent=2))
    else:
        if verbose > 0:
            print "Skipping deletion in repo {0} because not enough images.".format(repo)

    return deletion_tags

# >>>>>>>>>>>>>>>> MAIN STUFF

if __name__ == '__main__':

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

    repos_counts, repos = create_repo_list(args, reg_server_api)

    x = 0

    repo_tags_dates_digest, all_digests = get_all_tags_dates_digests(args.verbose, reg_server_api, repos,
                                                                     args.md_workers, args.cacert)

    if args.verbose > 2:
        print "List of all repos, tags, their creation dates and their digests:"
        print(json.dumps(repo_tags_dates_digest, indent=2))
        print all_digests

    diggests_occurrences = collections.Counter(all_digests)
    digests_counts = dict(diggests_occurrences)

    repo_del_tags = {}
    repo_del_digests = {}
    for repo, (count, tagname, date) in repos_counts.iteritems():
        x += 1
        update_progress(x, len(repos_counts))
        if args.verbose > 0:
            print
            print "will delete repo {0} and keep at least {1} images.".format(repo, count)
        del_tags = get_deletiontags(args.verbose, repo_tags_dates_digest[repo], repo, tagname, count, args.regex, date)

        if len(del_tags) > 0:
            repo_del_tags[repo] = del_tags
            repo_del_digests[repo] = set(deletion_digests(args.verbose, del_tags, digests_counts, args.ignoretag))

    answer = True
    if args.assumeyes is False and args.quiet is False and len(repo_del_digests) > 0:
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
                print "Deleting ", digest
                delete_manifest(args.verbose, reg_server_api, repo, digest, args.cacert)
    else:
        print "Aborted by user or nothing to delete."
        sys.exit(1)

    print
    print "Finished"
    sys.exit(0)
