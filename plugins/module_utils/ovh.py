from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    import ovh
    from ovh.exceptions import (
        APIError,
        InvalidKey,
        NotGrantedCall,
        BadParametersError,
        HTTPError,
        ResourceNotFoundError,
    )

    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def ovh_argument_spec():
    return dict(
        endpoint=dict(type="str", required=False, default=None),
        application_key=dict(type="str", required=False, default=None),
        application_secret=dict(type="str", required=False, default=None),
        consumer_key=dict(type="str", required=False, default=None),
    )


class OVHError(Exception):
    pass


class OVHResourceNotFound(Exception):
    pass


class OVH:
    def __init__(self, module):
        self.module = module

        self._validate()
        self._credentials()

        if all(self.credentials_in_parameters):
            self.client = ovh.Client(
                **{
                    credential: self.module.params[credential]
                    for credential in self.credentials
                }
            )
        else:
            self.client = ovh.Client()

    def _validate(self):
        if not HAS_OVH:
            self.module.fail_json(msg="python-ovh must be installed to use this module")

    def _credentials(self):
        self.credentials = [
            "endpoint",
            "application_key",
            "application_secret",
            "consumer_key",
        ]
        self.credentials_in_parameters = [
            cred in self.module.params for cred in self.credentials
        ]

    def get(self, path: str, **kwargs):
        return self._call(path, "GET", **kwargs)

    def put(self, path: str, **kwargs):
        return self._call(path, "PUT", **kwargs)

    def post(self, path: str, **kwargs):
        return self._call(path, "POST", **kwargs)

    def delete(self, path: str, **kwargs):
        return self._call(path, "DELETE", **kwargs)

    def _call(self, path: str, verb: str, **kwargs):
        """
        Wrapper for the calls to the api depending on the http verb.
        This allows to calls the right method to catch and raise errors.
        """
        try:
            if verb == "GET":
                return self.client.get(path, **kwargs)
            if verb == "PUT":
                return self.client.put(path, **kwargs)
            if verb == "POST":
                return self.client.post(path, **kwargs)
            if verb == "DELETE":
                return self.client.delete(path, **kwargs)
        except InvalidKey as e:
            self.module.fail_json(
                msg=f"Key {self.client._application_key}: {e}"
            )
        except BadParametersError as e:
            self.module.fail_json(msg=f"Invalid application_secret: {e}")
        except NotGrantedCall as e:
            self.module.fail_json(
                msg=f"Fails calling API {self.client._endpoint}{path}: {e}"
            )
        except HTTPError as e:
            self.module.fail_json(msg=f"Fails calling API: {e}")
        except APIError as e:
            self.module.fail_json(msg=f"Fails calling API: {e}")
        except ResourceNotFoundError:
            raise OVHResourceNotFound
