# encoding=utf-8
import ping

from ops_nd.plugins.utils import execute
import ops_nd.log as logging
from ops_nd.options import get_options

LOG = logging.getLogger(__name__)

ovs_opts = [
    {"name": "",
     "default": "",
     "help": "",
     "type": str
     },

]
options = get_options(ovs_opts)


class PhysicalOperation(object):
    def __init__(self, ip, user, password):
        self.ip = ip
        self.user = user
        self.password = password

    def reset_machine(self):
        try:
            cmd = ["ipmitool",
                   "-I",
                   "lan",
                   "-H",
                   "{0}".format(self.ip),
                   "-U",
                   "{0}".format(self.user),
                   "-P",
                   "{0}".format(self.password),
                   "power",
                   "reset"]
            ret = execute(cmd)
            if not ret[0]:
                return False, 500
            return True, 200
        except Exception as e:
            em = "reset machine error.... ip: <{0}> msg: <{1}>".format(self.ip, e)
            LOG.exception(em)
            return False, 500

    def boot_from_pxe(self):
        try:
            cmd = ["ipmitool",
                   "-I",
                   "lan",
                   "-H",
                   "{0}".format(self.ip),
                   "-U",
                   "{0}".format(self.user),
                   "-P",
                   "{0}".format(self.password),
                   "chassis",
                   "bootdev",
                   "pxe"]
            ret = execute(cmd)
            if not ret[0]:
                return False, 500
            return True, 200
        except Exception as e:
            em = "boot machine from pxe error.... ip: <{0}> msg: <{1}>".format(self.ip, e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def ping_host(dest_addr, timeout=0.1, psize=64):
        try:
            # packet size Maximum is 65507
            if psize > 65507:
                em = "Error: packet size {0} is too large. Maximum is 65507".format(psize)
                LOG.exception(em)
                return False
            ret = ping.do_one(dest_addr, timeout, psize)
            if not ret:
                return False
            return True
        except Exception as e:
            em = "ping error. ip: <{0}>. msg: <{1}>".format(dest_addr, e)
            LOG.exception(em)
            return False
