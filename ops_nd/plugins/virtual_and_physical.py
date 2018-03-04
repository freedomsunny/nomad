# encoding=utf-8
import json

import ops_nd.log as logging
from ops_nd.options import get_options
from ops_nd.utils import get_http, post_http
from ops_nd.plugins.openstack_handle import OpenStackHandle

LOG = logging.getLogger(__name__)

vp_opts = [
    {"name": "vp_network_ep",
     "default": "http://10.200.100.35:8913/api/v1.0/networks",
     "help": "get virtual&physical network",
     "type": str
     },

]
options = get_options(vp_opts)


class VPHandle(object):
    @staticmethod
    def get_network_info(network_uuid, token):
        try:
            headers = {'X-Auth-Token': token.strip()}
            ret = get_http(url=options.vp_network_ep, headers=headers)
            if ret.status_code != 200:
                em = "get network info error...."
                LOG.exception(em)
                return False, ret.status_code
            nets = ret.json()["networks"]
            for net in nets:
                if net.get("id") == network_uuid:
                    return net

        except Exception as e:
            em = "get network info error. msg: <{0}>".format(e)
            LOG.exception(em)
            return False, 500

