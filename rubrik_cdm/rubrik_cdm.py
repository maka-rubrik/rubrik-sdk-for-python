# Copyright 2018 Rubrik, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License prop
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module contains the Rubrik SDK Connect class.
"""

import base64
import requests
import os
import logging
from random import choice
import time

from .api import Api
from .cluster import Cluster
from .data_management import Data_Management
from .physical import Physical
from .cloud import Cloud
from .exceptions import InvalidParameterException, RubrikException, APICallException


_CLUSTER = Cluster
_DATA_MANAGEMENT = Data_Management
_PHYSICAL = Physical
_API = Api
_CLOUD = Cloud


class Connect(Cluster, Data_Management, Physical, Cloud):
    """This class acts as the base class for the Rubrik SDK and serves as the main interaction point
    for its end users. It also contains various helper functions used throughout the SDK.

    Arguments:
        _CLUSTER {class} -- This class contains methods related to the management of the Rubrik Cluster itself.
        _DATA_MANAGEMENT {class} - This class contains methods related to backup and restore operations for the various objects managed by the Rubrik Cluster.
        _PHYSICAL {class} - This class contains methods related to the management of the Physical objects in the Rubrik Cluster.
    """

    def __init__(self, node_ip=None, username=None, password=None, api_token=None, enable_logging=False):
        """Constructor for the Connect class which is used to initialize the class variables.

        Keyword Arguments:
            node_ip {str} -- The Hostname or IP Address of a node in the Rubrik cluster you wish to connect to. If a value is not provided we will check for a `rubrik_cdm_node_ip` environment variable. (default: {None})
            username {str} -- The Username you wish to use to connect to the Rubrik cluster. If a value is not provided we will check for a `rubrik_cdm_username` environment variable. (default: {None})
            password {str} -- The Password you wish to use to connect to the Rubrik cluster. If a value is not provided we will check for a `rubrik_cdm_password` environment variable. (default: {None})
            api_token {str} -- The API Token you wish to use to connect to the Rubrik cluster. If populated, the `username` and `password` fields will be ignored. If a value is not provided we will check for a `rubrik_cdm_token` environment variable.  (default: {None})
            enable_logging {bool} -- Flag to determine if logging will be enabled for the SDK. (default: {False})
        """

        if enable_logging:
            logging.getLogger().setLevel(logging.DEBUG)

        if node_ip is None:
            node_ip = os.environ.get('rubrik_cdm_node_ip')
            if node_ip is None:
                raise InvalidParameterException("The Rubrik CDM Node IP has not been provided.")
            else:
                self.node_ip = node_ip
        else:
            self.node_ip = node_ip

        self.log("Node IP: {}".format(self.node_ip))

        # If the api_token has not been provided check for the env variable and then
        # check for the username and password fields
        if api_token is None:
            api_token = os.environ.get('rubrik_cdm_token')
            if api_token is None:

                self.api_token = None

                if username is None:
                    username = os.environ.get('rubrik_cdm_username')
                    if username is None:
                        raise InvalidParameterException(
                            "The Rubrik CDM Username or an API Token has not been provided.")
                    else:
                        self.username = username
                        self.log("Username: {}".format(self.username))
                else:
                    self.username = username
                    self.log("Username: {}".format(self.username))

                if password is None:
                    password = os.environ.get('rubrik_cdm_password')
                    if password is None:
                        raise InvalidParameterException(
                            "The Rubrik CDM Password or an API Token has not been provided.")
                    else:
                        self.password = password
                        self.log("Password: *******\n")
                else:
                    self.password = password
                    self.log("Password: *******\n")

            else:
                self.api_token = api_token
                self.log("API Token: *******\n")
        else:
            self.api_token = api_token
            self.log("API Token: *******\n")

    @staticmethod
    def log(log_message):
        """Create properly formatted debug log messages.

        Arguments:
            log_message {str} -- The message to pass to the debug log.
        """
        log = logging.getLogger(__name__)
        log.debug(log_message)

    def _authorization_header(self):
        """Internal method used to create the authorization header used in the API calls.

        Returns:
            dict -- The authorization header that utilizes Basic authentication.
        """

        if self.api_token is None:
            self.log("Creating the authorization header using the provided username and password.")

            credentials = '{}:{}'.format(self.username, self.password)

            # Encode the Username:Password as base64
            authorization = base64.b64encode(credentials.encode())
            # Convert to String for API Call
            authorization = authorization.decode()

            authorization_header = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Basic ' + authorization,
                'User-Agent': 'Rubrik Python SDK v1.0.13'
            }

        else:

            self.log("Creating the authorization header using the provided API Token.")
            authorization_header = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + self.api_token,
                'User-Agent': 'Rubrik Python SDK v1.0.13'
            }

        return authorization_header

    @staticmethod
    def _header():
        """Internal method used to create the a header without authorization used in the API calls.

        Returns:
            dict -- The header that does not include any authorization.
        """

        header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        return header

    @staticmethod
    def _api_validation(api_version, api_endpoint):
        """Internal method used to validate the API Version and API Endpoint provided by the end user

        Arguments:
            api_version {str} -- The version of the Rubrik CDM API to call. (choices: {v1, v2, internal})
            api_endpoint {str} -- The endpoint of the Rubrik CDM API to call (ex. /cluster/me).
        """

        valid_api_versions = ['v1', 'v2', 'internal']

        # Validate the API Version
        if api_version not in valid_api_versions:
            raise InvalidParameterException(
                "Enter a valid API version {}.".format(valid_api_versions))

        # Validate the API Endpoint Syntax
        if not isinstance(api_endpoint, str):
            raise InvalidParameterException("The API Endpoint must be a string.")
        elif api_endpoint[0] != "/":
            raise InvalidParameterException(
                "The API Endpoint should begin with '/'. (ex: /cluster/me)")
        elif api_endpoint[-1] == "/":
            if api_endpoint[-2] != "=":
                raise InvalidParameterException(
                    "Error: The API Endpoint should not end with '/' unless proceeded by '='. (ex. /cluster/me or /fileset/snapshot/<id>/browse?path=/)")



class Bootstrap(_API):
    """This class contains all functions related to the Bootstrapping of a Rubrik Cluster.

    Arguments:
        _API {class} - This class contains the base API methods that can be called independently or internally in standalone functions.
    """

    def __init__(self, node_ip, enable_logging=False):
        """Constructor for the Bootstrap class which is used to initialize the class variables.
        """

        if enable_logging:
            logging.getLogger().setLevel(logging.DEBUG)

        self.node_ip = node_ip
        self.log("User Provided Node IP: {}".format(self.node_ip))

        node_ip = [self.node_ip]

    def setup_cluster(self, cluster_name, admin_email, admin_password, management_gateway, management_subnet_mask, node_config=None,
                      enable_encryption=True, dns_search_domains=None, dns_nameservers=None, ntp_servers=None, wait_for_completion=True, timeout=30):
        """Issues a bootstrap request to a specified Rubrik cluster

        Arguments:
            cluster_name {str} -- Unique name to assign to the Rubrik cluster.
            admin_email {str} -- The Rubrik cluster sends messages for the admin account to this email address.
            admin_password {str} --  Password for the admin account.
            management_gateway {str} --  IP address assigned to the management network gateway
            management_subnet_mask {str} -- Subnet mask assigned to the management network.

        Keyword Arguments:
            node_config {dict} -- The Node Name and IP formatted as a dictionary. (default: {None})
            enable_encryption {bool} -- Enable software data encryption at rest. When bootstraping a Cloud Cluster this value needs to be False. (default: {True})
            dns_search_domains {str} -- The search domain that the DNS Service will use to resolve hostnames that are not fully qualified. (default: {None})
            dns_nameservers {list} -- IPv4 addresses of DNS servers. (default: {['8.8.8.8']})
            ntp_servers {list} -- FQDN or IPv4 address of a network time protocol (NTP) server. (default: {['pool.ntp.org']})
            wait_for_completion {bool} -- Flag to determine if the function should wait for the bootstrap process to complete. (default: {True})
            timeout {int} -- The number of seconds to wait to establish a connection the Rubrik cluster before returning a timeout error. (default: {30})

        Returns:
            dict -- The response returned by `POST /internal/cluster/me/bootstrap`.
        """

        if node_config is None or isinstance(node_config, dict) is not True:
            raise InvalidParameterException(
                'You must provide a valid dictionary for "node_config".')

        if dns_search_domains is None:
            dns_search_domains = []
        elif isinstance(dns_search_domains, list) is not True:
            raise InvalidParameterException(
                'You must provide a valid list for "dns_search_domains".')

        if dns_nameservers is None:
            dns_nameservers = ['8.8.8.8']
        elif isinstance(dns_nameservers, list) is not True:
            raise InvalidParameterException('You must provide a valid list for "dns_nameservers".')

        if ntp_servers is None:
            ntp_servers = ['pool.ntp.org']
        elif isinstance(ntp_servers, list) is not True:
            raise InvalidParameterException('You must provide a valid list for "ntp_servers".')

        bootstrap_config = {}
        bootstrap_config["enableSoftwareEncryptionAtRest"] = enable_encryption
        bootstrap_config["name"] = cluster_name
        bootstrap_config["dnsNameservers"] = dns_nameservers
        bootstrap_config["dnsSearchDomains"] = dns_search_domains
        bootstrap_config["ntpServers"] = ntp_servers

        bootstrap_config["adminUserInfo"] = {}
        bootstrap_config["adminUserInfo"]['password'] = admin_password
        bootstrap_config["adminUserInfo"]['emailAddress'] = admin_email
        bootstrap_config["adminUserInfo"]['id'] = "admin"

        bootstrap_config["nodeConfigs"] = {}
        for node_name, node_ip in node_config.items():
            bootstrap_config["nodeConfigs"][node_name] = {}
            bootstrap_config["nodeConfigs"][node_name]['managementIpConfig'] = {}
            bootstrap_config["nodeConfigs"][node_name]['managementIpConfig']['netmask'] = management_subnet_mask
            bootstrap_config["nodeConfigs"][node_name]['managementIpConfig']['gateway'] = management_gateway
            bootstrap_config["nodeConfigs"][node_name]['managementIpConfig']['address'] = node_ip

        while True:

            try:
                self.log('bootstrap: Starting the bootstrap process.')
                number_of_attempts = 1
                api_request = self.post(
                    'internal',
                    '/cluster/me/bootstrap',
                    bootstrap_config,
                    timeout,
                    authentication=False)
                break
            except APICallException as bootstrap_error:
                if "Failed to establish a new connection: [Errno 111] Connection refused" in str(
                        bootstrap_error):
                    self.log(
                        'bootstrap: Connection refused. Waiting 30 seconds for the node to initialize before trying again.')
                    number_of_attempts += 1
                    time.sleep(30)
                elif "Cannot bootstrap from an already bootstrapped node" in str(bootstrap_error):
                    return "No change required. The Rubrik cluster is already bootstrapped."
                else:
                    self.log('bootstrap: Connection refused.')
                    raise RubrikException(bootstrap_error)

            if number_of_attempts == 12:
                raise APICallException(
                    "Unable to establish a connection to the Rubrik cluster.")

        request_id = api_request['id']

        if wait_for_completion:
            self.log('bootstrap: Waiting for the bootstrap process to complete.')
            while True:
                status = self.status(request_id)

                if status['status'] == 'IN_PROGRESS':
                    self.log("bootstrap_status: {}\n".format(status))
                    time.sleep(30)
                    continue
                elif status['status'] == 'FAILURE' or status['status'] == "FAILED":
                    raise RubrikException("{}".format(status['message']))
                else:
                    self.log("{}".format(status))
                    return status

        return api_request

    def status(self, request_id="1", timeout=15):
        """Retrieves status of in progress bootstrap requests

        Keyword Arguments:
            request_id {str} -- ID of the bootstrap request(default: {"1"})
            timeout {int} -- The response timeout value, in seconds, of the API call. (default: {15})

        Returns:
            dict -- The response returned by `GET /internal/cluster/me/bootstrap?request_id={request_id}`.
        """

        self.log('status: Getting the status of the Rubrik Cluster bootstrap.')
        bootstrap_status_api_endpoint = '/cluster/me/bootstrap?request_id={}'.format(
            request_id)
        api_request = self.get(
            'internal', bootstrap_status_api_endpoint, timeout=timeout, authentication=False)

        return api_request

    def discover(self, timeout=30):
        """Searches for nodes bootstrappable to the specified Rubrik cluster

        Keyword Arguments:
            timeout {int} -- The response timeout value, in seconds, of the API call. (default: {30})

        Returns:
            dict -- The response returned by `GET /internal/cluster/me/discover`.
        """

        self.log('status: Discovering bootstrappable nodes for the Rubrik Cluster.')
        discover_api_endpoint = '/cluster/me/discover'
        api_request = self.get(
            'internal', discover_api_endpoint, timeout=timeout, authentication=False)

        return api_request

    @staticmethod
    def log(log_message):
        """Create properly formatted debug log messages.

        Arguments:
            log_message {str} - - The message to pass to the debug log.
        """
        log = logging.getLogger(__name__)
        log.debug(log_message)

    @staticmethod
    def _header():
        """Internal method used to create the a header without authorization used in the API calls.

        Returns:
            dict - - The header that does not include any authorization.
        """

        header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        return header

    @staticmethod
    def _api_validation(api_version, api_endpoint):
        """Internal method used to validate the API Version and API Endpoint provided by the end user

        Arguments:
            api_version {str} - - The version of the Rubrik CDM API to call.
            api_endpoint {str} - - The endpoint(ex. cluster / me) of the Rubrik CDM API to call.
        """

        valid_api_versions = ['v1', 'internal']

        # Validate the API Version
        if api_version not in valid_api_versions:
            raise InvalidParameterException(
                "Enter a valid API version {}.".format(valid_api_versions))

        # Validate the API Endpoint Syntax
        if not isinstance(api_endpoint, str):
            raise InvalidParameterException("The API Endpoint must be a string.")
        elif api_endpoint[0] != "/":
            raise InvalidParameterException(
                "The API Endpoint should begin with '/'. (ex: /cluster/me)")
        elif api_endpoint[-1] == "/":
            if api_endpoint[-2] != "=":
                raise InvalidParameterException(
                    "Error: The API Endpoint should not end with '/' unless proceeded by '='. (ex. /cluster/me or /fileset/snapshot/<id>/browse?path=/)")
