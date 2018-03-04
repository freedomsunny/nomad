# encoding=utf-8
import xmlrpclib

import ops_nd.log as logging
from ops_nd.options import get_options


LOG = logging.getLogger(__name__)

ovs_opts = [
    {"name": "cobbler_api",
     "default": "http://172.16.130.2/cobbler_api",
     "help": "cobbler server api",
     "type": str
     },
    {"name": "cobbler_user",
     "default": "admin",
     "help": "cobbler server api user",
     "type": str
     },
    {"name": "cobbler_password",
     "default": "5fa94ab741f60417db51",
     "help": "cobbler server api password",
     "type": str
     },
    {"name": "finish_ep",
     # "default": "http://manage.xiangcloud.com.cn:8900/order/orders",
     "default": "http://122.115.50.247:8915/physical/finish",
     "help": "when physical machine finished install. call this api",
     "type": str
     },
]
options = get_options(ovs_opts)


class CobblerOperation(object):

    def __init__(self, user=options.cobbler_user, password=options.cobbler_password, cobbler_api=options.cobbler_api):
        self.remote = xmlrpclib.Server(cobbler_api)
        self.token = self.remote.login(user, password)
        self.system_id = self.remote.new_system(self.token)

    def add_cobbler_system(self, cobbler_ip, cobbler_mask, cobbler_mac, cobbler_profile, cobbler_sysname, ip_addr, password,
                           mask, gateway="", host_name="xy_cloud", dns="114.114.114.114", physical_id=""):
        """add host system to cobbler server
        #  system kickstart meta data define
        IP_ADDRESS:    system's ip address
        PASSWORD:   system's root password
        MASK:     ip address prefix
        DNS:        name server address
        GATEWAY:    network's gateway
        PHYSICAL_ID: physical id in db
        FINISH_EP: when physical machine finished install. call this api
        """
        try:
                data = {"macaddress-eth0": cobbler_mac,
                        "ipaddress-eth0": cobbler_ip,
                        "subnet-eth0": cobbler_mask,
                        }
                ks_meta_data = "IP_ADDRESS={0} PASSWORD={1} MASK={2} DNS={3} GATEWAY={4} PHYSICAL_ID={5} FINISH_EP={6}"\
                    .format(ip_addr, password, mask, dns, gateway, physical_id, options.finish_ep)
                kernel_ops = "net.ifnames=0 biosdevname=0"
                host_name = host_name + "-" + ip_addr.replace('.', "-")
                assert self.remote.modify_system(self.system_id, "name", cobbler_sysname, self.token)
                assert self.remote.modify_system(self.system_id, "hostname", host_name, self.token)
                assert self.remote.modify_system(self.system_id, 'modify_interface', data, self.token)
                assert self.remote.modify_system(self.system_id, "profile", cobbler_profile, self.token)
                assert self.remote.modify_system(self.system_id, "ks_meta", "{0}".format(ks_meta_data), self.token)
                assert self.remote.modify_system(self.system_id, "kernel_options", "{0}".format(kernel_ops), self.token)
                assert self.remote.save_system(self.system_id, self.token)
                assert self.remote.sync(self.token)
                return True, 200
        except Exception as e:
            em = "add cobbler system error. host ip: <{0}> msg:<{1}>".format(cobbler_ip, e)
            LOG.exception(em)
            return False, 500

    def remove_cobbler_system(self, system_name):
        try:
            assert self.remote.remove_system(system_name, self.token)
            return True, 200
        except Exception as e:
            em = "remove cobbler system error. msg: <{0}>".format(e)
            LOG.exception(em)
            return False, 500

    def get_profiles(self):
        return self.remote.get_profiles()
