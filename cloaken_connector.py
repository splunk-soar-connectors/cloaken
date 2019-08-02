# -----------------------------------------
# Phantom sample App Connector python file
# -----------------------------------------

# Phantom App imports
import phantom.app as phantom
from phantom.base_connector import BaseConnector
from phantom.action_result import ActionResult

import json
from bs4 import BeautifulSoup
from cloakensdk.client import SyncClient
from cloakensdk.resources import Url


class RetVal(tuple):
    def __new__(cls, val1, val2=None):
        return tuple.__new__(RetVal, (val1, val2))


class CloakenConnector(BaseConnector):

    def __init__(self):

        super(CloakenConnector, self).__init__()

        self._state = None
        self._base_url = None

    def _process_empty_response(self, response, action_result):

        if response.status_code == 200:
            return RetVal(phantom.APP_SUCCESS, {})

        return RetVal(action_result.set_status(phantom.APP_ERROR, "Empty response and no information in the header."), None)

    def _process_html_response(self, response, action_result):

        # An html response, treat it like an error
        status_code = response.status_code

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            error_text = soup.text
            split_lines = error_text.split('\n')
            split_lines = [x.strip() for x in split_lines if x.strip()]
            error_text = '\n'.join(split_lines)
        except:
            error_text = "Cannot parse error details"

        message = "Status Code: {0}. Data from server:\n{1}\n".format(status_code,
                error_text)

        message = message.replace(u'{', '{{').replace(u'}', '}}')

        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _process_json_response(self, r, action_result):

        # Try a json parse
        try:
            resp_json = r.json()
        except Exception as e:
            return RetVal(action_result.set_status(phantom.APP_ERROR, "Unable to parse JSON response. Error: {0}".format(str(e))), None)

        # do not stop on 400 error; that is a malformed url or dead link
        if r.status_code == 400:
            return RetVal(phantom.APP_SUCCESS, resp_json)

        if 200 <= r.status_code < 399:
            return RetVal(phantom.APP_SUCCESS, resp_json)

        message = "Error from server. Status Code: {0} Data from server: {1}".format(
                r.status_code, r.text.replace(u'{', '{{').replace(u'}', '}}'))

        return RetVal(action_result.set_status(phantom.APP_ERROR, message),
                None)

    def _process_response(self, r, action_result):

        if hasattr(action_result, 'add_debug_data'):
            action_result.add_debug_data({'r_status_code': r.status_code})
            action_result.add_debug_data({'r_text': r.text})
            action_result.add_debug_data({'r_headers': r.headers})

        # Process a json response
        if 'json' in r.headers.get('Content-Type', ''):
            return self._process_json_response(r, action_result)

        # Process an HTML response, Do this no matter what the api talks.
        # There is a high chance of a PROXY in between phantom and the rest of
        # world, in case of errors, PROXY's return HTML, this function parses
        # the error and adds it to the action_result.
        if 'html' in r.headers.get('Content-Type', ''):
            return self._process_html_response(r, action_result)

        # it's not content-type that is to be parsed, handle an empty response
        if not r.text:
            return self._process_empty_response(r, action_result)

        # everything else is actually an error at this point
        message = "Can't process response from server. Status Code: {0} Data from server: {1}".format(
                r.status_code, r.text.replace('{', '{{').replace('}', '}}'))
        self.save_progress("error:" + message)
        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _handle_test_connectivity(self, param):

        # Add an action result object to self (BaseConnector) to represent the action for this param
        action_result = self.add_action_result(ActionResult(dict(param)))

        self.save_progress("Connecting to endpoint")
        ret_val, data = self._process_response(self.client.login_response, action_result)

        if (phantom.is_fail(ret_val)):
            action_result.set_status(phantom.APP_ERROR)
            # the call to the 3rd party device or service failed, action result should contain all the error details
            # for now the return is commented out, but after implementation, return from here
            self.save_progress("Test Connectivity Failed. " + str(ret_val))
            return action_result.get_status()

        self.save_progress("Test Connectivity Passed")
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_lookup_url(self, param):

        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        action_result = self.add_action_result(ActionResult(dict(param)))

        url = param['url']

        # make rest call
        resource = Url(self.client)
        resource.unshorten(url)
        self.save_progress("resource claimed: {0}".format(self.get_action_identifier()))
        response = resource.request(self)
        self.save_progress("request done: {0}".format(self.get_action_identifier()))
        ret_val, data = self._process_response(response, action_result)

        self.save_progress("request processed: {0}".format(self.get_action_identifier()))

        if (phantom.is_fail(ret_val)):
            return action_result.get_status()
        else:
            action_result.add_data(data)

        self.save_progress("data {0}".format(str(data)))
        if response.status_code == 400:
            action_result.update_summary({"original_url": url,
                "error": data["url"]})
        else:
            action_result.update_summary({"original_url": url,
                "unshortened_url": data["unshortened_url"]})

        return action_result.set_status(phantom.APP_SUCCESS)

    def handle_action(self, param):

        ret_val = phantom.APP_SUCCESS

        self.save_progress("In handle action for: {0}".format(self.get_action_identifier()))

        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id == 'test_connectivity':
            ret_val = self._handle_test_connectivity(param)

        elif action_id == 'lookup_url':
            ret_val = self._handle_lookup_url(param)

        return ret_val

    def initialize(self):

        self._state = self.load_state()

        config = self.get_config()

        self.save_progress("Ininitialize: ")
        self._base_url = config.get('server_url')
        self.username = config["username"]
        self.password = config["password"]
        try:
            self.client = SyncClient(server_url=self._base_url, username=self.username,
                    password=self.password)
        except Exception as e:
            try:
                return self.set_status(phantom.APP_ERROR, str(e).encode('utf-8'))
            except:
                return self.set_status(phantom.APP_ERROR, "Error occurred while creating the client. Please verify the provided asset configuration parameters.")

        return phantom.APP_SUCCESS

    def finalize(self):

        self.save_state(self._state)
        return phantom.APP_SUCCESS


if __name__ == '__main__':

    import pudb
    import argparse

    pudb.set_trace()

    argparser = argparse.ArgumentParser()

    argparser.add_argument('input_test_json', help='Input Test JSON file')
    argparser.add_argument('-u', '--username', help='username', required=False)
    argparser.add_argument('-p', '--password', help='password', required=False)

    args = argparser.parse_args()
    session_id = None

    username = args.username
    password = args.password

    if (username is not None and password is None):

        import getpass
        password = getpass.getpass("Password: ")

    if (username and password):
        try:

            print ("Accessing the Login page")

            data = dict()
            data['username'] = username
            data['password'] = password

            print ("Logging into Platform to get the session id")
        except Exception as e:
            print ("Unable to get session id from the platform. Error: " + str(e))
            exit(1)

    with open(args.input_test_json) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = CloakenConnector()
        connector.print_progress_message = True

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print (json.dumps(json.loads(ret_val), indent=4))

    exit(0)
