# encoding=utf-8
import json

from ops_nd.plugins.utils import execute
import ops_nd.log as logging
from ops_nd.options import get_options
from ops_nd.plugins.openstack_handle import OpenStackHandle
from ops_nd.utils import get_http, post_http, delete_http

LOG = logging.getLogger(__name__)

sw_opts = [
    {"name": "sdn_sw_ep",
     # "default": "http://10.200.100.35:8913/api/v1.0/switch/sdn",
     "default": "http://10.200.100.35:8913/api/v1.0/switch/sdn",
     "help": "sdn switch end point",
     "type": str
     },
    {"name": "l2_sw_ep",
     # "default": "http://10.200.100.35:8913/api/v1.0/switch/l2switch",
     "default": "http://10.200.100.35:8913/api/v1.0/switch/l2switch",
     "help": "layer 2 switch end point",
     "type": str
     },

]
options = get_options(sw_opts)


class L2SwitchConfig(object):
    @staticmethod
    def sw_delete_port(network_id, sw_ip, sw_password, sw_username, token, sw_port):
        try:
            # set l2 switch port to access 4094
            data = {"network_id": network_id,
                    "sw_ip": sw_ip,
                    "sw_pwd": sw_password,
                    "sw_user": sw_username,
                    "sw_port": sw_port
                    }
            headers = {'X-Auth-Token': token.strip(),
                       'Content-type': 'application/json'}
            data = json.dumps(data)
            ret = delete_http(url=options.l2_sw_ep, data=data, headers=headers)
            if ret.status_code != 200:
                em = "config l2 switch error. switch ip: <{0}> switch port: <{1}>".format(sw_ip,
                                                                                          sw_port)
                LOG.exception(em)
                return False, 500
            return True, 200
        except Exception as e:
            em = "config l2 switch error. switch ip: <{0}>, msg: <{1}>".format(sw_ip, e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def sw_add_port(network_id, sw_ip, sw_password, sw_username, token, sw_port):
        try:
            # set l2 switch port to access 4094
            data = {"network_id": network_id,
                    "sw_ip": sw_ip,
                    "sw_pwd": sw_password,
                    "sw_user": sw_username,
                    "sw_port": sw_port}
            headers = {'X-Auth-Token': token.strip(),
                       'Content-type': 'application/json'}
            data = json.dumps(data)
            ret = post_http(url=options.l2_sw_ep, data=data, headers=headers)
            if ret.status_code != 200:
                em = "config l2 switch error. switch ip: <{0}> switch port: <{1}>".format(sw_ip, sw_port)
                LOG.exception(em)
                return False, 500
            return True, 200
        except Exception as e:
            em = "l2 switch config error. switch ip: <{0}>. msg: <{1}>".format(sw_ip, e)
            LOG.exception(em)
            return False, 500


class SDNSwitchConfig(object):
    @staticmethod
    def sw_delete_vtep(sw_sdn_ips, network_id, sw_password, sw_username, token):
        try:
            for sw_sdn_ip in sw_sdn_ips:
                data = {"network_id": network_id,
                        "sw_ip": sw_sdn_ip,
                        "sw_pwd": sw_password,
                        "sw_user": sw_username}
                data = json.dumps(data)
                headers = {'X-Auth-Token': token.strip(),
                           'Content-type': 'application/json'}
                ret = delete_http(url=options.sdn_sw_ep, headers=headers, data=data)
                if ret.status_code != 200:
                    em = "config sdn switch error. switch ip: <{0}>".format(sw_sdn_ip)
                    LOG.exception(em)
                    return False, 500
            return True, 200
        except Exception as e:
            em = "config sdn switch error. switch ip: <{0}>. msg: <{1}>".format(sw_sdn_ip, e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def sw_add_vtep(sw_ips, network_id, sw_password, sw_username, token):
        try:
            for sw_sdn_ip in sw_ips:
                data = {"network_id": network_id,
                        "sw_ip": sw_sdn_ip,
                        "sw_pwd": sw_password,
                        "sw_user": sw_username}
                data = json.dumps(data)
                headers = {'X-Auth-Token': token.strip(),
                           'Content-type': 'application/json'}
                ret = post_http(url=options.sdn_sw_ep, headers=headers, data=data)
                if ret.status_code != 200:
                    em = "config sdn switch error. switch ip: <{0}>".format(sw_sdn_ip)
                    LOG.exception(em)
                    return False, 500
            return True, 200
        except Exception as e:
            em = "config sdn switch error. switch ip: <{0}>. msg: <{1}>".format(sw_sdn_ip, e)
            LOG.exception(em)
            return False, 500
