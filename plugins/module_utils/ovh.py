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
        ResourceNotFoundError
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

    def wrap_call(self, verb: str, path: str, _need_auth: bool = True, **kwargs):
        """
        Wrapper for the call to the api. Set kwargs using methods from the ovh module.

        Args:
            verb: http verb to use for the call.
            path: API route to call.
            _need_auth: If True, send authentication headers. This is the default.
        """
        # This is copied from the OVH python module
        # https://github.com/ovh/python-ovh/blob/master/ovh/client.py#L330
        if kwargs:
            kwargs = self.client._canonicalize_kwargs(kwargs)
            if verb in ["GET", "DELETE"]:
                query_string = self.client._prepare_query_string(kwargs)
                if query_string != "":
                    if "?" in path:
                        path = f"{path}&{query_string}"
                    else:
                        path = f"{path}?{query_string}"
        if not kwargs:
            kwargs = None

        try:
            return self.client.call(verb, path, kwargs, _need_auth)

        except InvalidKey as e:
            self.module.fail_json(
                msg=f"Key {self.client._application_key}: {e}"
            )
        except BadParametersError as e:
            self.module.fail_json(msg=f"Invalid application_secret: {e}")
        except NotGrantedCall as e:
            self.module.fail_json(
                msg=f"Fails calling API ({verb} {self.client._endpoint}{path}): {e}"
            )
        except HTTPError as e:
            self.module.fail_json(msg=f"Fails calling API ({verb} {self.client._endpoint}{path}): {e}")
        except APIError as e:
            self.module.fail_json(msg=f"Fails calling API ({verb} {self.client._endpoint}{path}): {e}")
        except ResourceNotFoundError:
            raise OVHResourceNotFound
