# encoding=utf-8
import json

from ops_nd.plugins.utils import execute
import ops_nd.log as logging
from ops_nd.options import get_options
from ops_nd.utils import get_http, post_http

LOG = logging.getLogger(__name__)

ovs_opts = [
    {"name": "flow_control_ep",
     "default": "http://10.200.100.8:8914/network/flowoperation_ser",
     "help": "OpenStack flow control API",
     "type": str
     },
]
options = get_options(ovs_opts)


class AddFlow2OpenStack(object):
    @staticmethod
    def add_flow2os(ip, mac, network_id):
        data = {"ip": ip,
                "mac": mac,
                "network_id": network_id,
                }
        data = json.dumps(data)
        ret = post_http(url=options.flow_control_ep, data=data)
        if ret.status_code != 200:
            return False, 500
        return True, 200
