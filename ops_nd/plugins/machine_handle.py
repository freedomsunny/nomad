# encoding=utf-8
import json
import time
import uuid
from IPy import IP


import ops_nd.log as logging
from ops_nd.options import get_options
from ops_nd.utils import get_http, post_http, delete_http
from ops_nd.plugins.cobbler_handle import CobblerOperation
from ops_nd.plugins.openstack_handle import OpenStackHandle
from ops_nd.plugins.physical_handle import PhysicalOperation
from ops_nd.plugins.flow_handle import AddFlow2OpenStack
from ops_nd.plugins.cmdb_handle import CMDBHandle
from ops_nd.plugins.switch_handle import L2SwitchConfig, SDNSwitchConfig
from ops_nd.db.api import PhysicalTable
from ops_nd.db.api import *
LOG = logging.getLogger(__name__)

ovs_opts = [
    {"name": "charging_ep",
     # "default": "http://manage.xiangcloud.com.cn:8900/order/orders",
     "default": "http://122.115.50.247:8900/order/orders",
     "help": "charging end point",
     "type": str
     },

]
options = get_options(ovs_opts)


class MachineOperation(object):
    @staticmethod
    def create_physical(data_obj):
        try:
            # apply port from OpenStack
            ret = OpenStackHandle.apply_port(data_obj.tenant_project_id,
                                             data_obj.tenant_network_id,
                                             data_obj.tenant_subnet_id,
                                             data_obj.tenant_mac)
            if not ret[0]:
                em = "apply ip address from OpenStack error. network id: <{0}>. subnet id: <{1}>".format(data_obj.tenant_network_id,
                                                                                                         data_obj.tenant_subnet_id)
                LOG.exception(em)
                raise StandardError(em)
            data_obj.tenant_port_id = ret[1].get('port').get('id')
            data_obj.tenant_ip = ret[1].get('port').get('fixed_ips')[0].get('ip_address')
            data_obj.cobbler_sysname = data_obj.cobbler_profile + "_" + data_obj.tenant_ip.replace(".", "-")
            LOG.debug("apply port from OpenStack with successful. ip: <{0}> port id: <{1}>".format(data_obj.tenant_ip,
                                                                                                   data_obj.tenant_port_id))
            # check system name is it exist
            ret = PhysicalTable.select_by_userid_sysname(data_obj.tenant_user_id,
                                                         data_obj.cobbler_sysname)
            if ret:
                em = "add cobbler system error. system name <{0}> is already exist".format(data_obj.cobbler_sysname)
                LOG.exception(em)
                raise StandardError(em)
            #  add cobbler system.
            cb_obj = CobblerOperation()
            ret = cb_obj.add_cobbler_system(data_obj.cobbler_ip,
                                            data_obj.cobbler_mask,
                                            data_obj.cobbler_mac,
                                            data_obj.cobbler_profile,
                                            data_obj.cobbler_sysname,
                                            data_obj.tenant_ip,
                                            data_obj.tenant_sys_password,
                                            data_obj.tenant_mask,
                                            data_obj.tenant_gateway,
                                            physical_id=data_obj.physical_id
                                            )
            if not ret[0]:
                em = "add cobbler system error. system name: <{0}>".format(data_obj.cobbler_sysname)
                LOG.exception(em)
                raise StandardError(em)
            LOG.debug("add system to cobbler server with successful. system name: <{0}>".format(data_obj.cobbler_sysname))
            # reset physical machine
            phy_obj = PhysicalOperation(data_obj.ipmi_ip,
                                        data_obj.ipmi_username,
                                        data_obj.ipmi_password)
            ret = phy_obj.boot_from_pxe()
            if not ret[0]:
                em = "boot from pxe error. ipmi ip: <{0}>".format(data_obj.ipmi_ip)
                LOG.exception(em)
                raise StandardError(em)
            LOG.debug("server boot from pxe by ipmi with successful. server ip: <{0}>".format(data_obj.ipmi_ip))
            ret = phy_obj.reset_machine()
            if not ret[0]:
                em = "restart pipmi error. ipmi ip: <{0}>".format(data_obj.ipmi_ip)
                LOG.exception(em)
                raise StandardError(em)
            LOG.debug("reset server by ipmi with successful. server ip: <{0}>".format(data_obj.ipmi_ip))
            # config l2 switch
            ret = L2SwitchConfig.sw_add_port(data_obj.tenant_network_id,
                                             data_obj.sw_l2_ip,
                                             data_obj.sw_l2_password,
                                             data_obj.sw_l2_username,
                                             data_obj.tenant_token.strip(),
                                             data_obj.sw_l2_port
                                             )
            if not ret[0]:
                em = "config l2 switch error. switch ip: <{0}> switch port: <{1}>".format(data_obj.sw_l2_ip,
                                                                                          data_obj.sw_l2_port)
                LOG.exception(em)
                raise StandardError(em)
            LOG.debug("config l2 switch with successful. l2 switch ip: <{0}>".format(data_obj.sw_l2_ip))

            # config sdn switch. sdn switch maybe is multi
            ret = SDNSwitchConfig.sw_add_vtep(data_obj.sw_sdn_ips,
                                              data_obj.tenant_network_id,
                                              data_obj.sw_sdn_passowrd,
                                              data_obj.sw_sdn_username,
                                              data_obj.tenant_token.strip()
                                              )

            if not ret[0]:
                em = "config sdn switch error. switch ip: <{0}>".format(data_obj.sw_sdn_ips)
                LOG.exception(em)
                raise StandardError(em)

            LOG.debug("config sdn switch with successful. sdn switch ip: <{0}>".format(data_obj.sw_sdn_ips))
            #
            # # add flow(OpenStack)
            # ret = AddFlow2OpenStack.add_flow2os(data_obj.tenant_ip,
            #                                     data_obj.tenant_mac,
            #                                     data_obj.tenant_network_id)
            # if not ret[0]:
            #     em = "add flow to OpenStack error. ip: <{0}> network id: <{1}>".format(data_obj.tenant_ip,
            #                                                                            data_obj.tenant_network_id)
            #     LOG.exception(em)
            #     raise StandardError(em)

            # update physical machine's status in cmdb
            ret = CMDBHandle.update_physical_status(data_obj.cmdb_uuid, u"已用")
            if not ret[0]:
                em = "error update cmdb's status.cmdb uuid: <{0}>".format(data_obj.cmdb_uuid)
                LOG.exception(em)
                raise StandardError(em)
            LOG.debug("update cmdb's status with successful. cmdb uuid: <{0}>".format(data_obj.cmdb_uuid))
            # add info to db
            data = {"id": data_obj.physical_id,
                    "cobbler_sysname": data_obj.cobbler_sysname,
                    "tenant_hostname": data_obj.tenant_hostname,
                    "user_id": data_obj.tenant_user_id,
                    "user_name": data_obj.tenant_user_name,
                    "project_id": data_obj.tenant_project_id,
                    "tenant_ip": data_obj.tenant_ip,
                    "tenant_port_id": data_obj.tenant_port_id,
                    "password": data_obj.tenant_sys_password,
                    "cmdb_uuid": data_obj.cmdb_uuid,
                    "network_uuid": data_obj.network_uuid,
                    "status": "installing"
                    }
            ret = PhysicalTable.add_data(data)
            if not ret:
                em = "add cobbler info to db error.........."
                LOG.exception(em)
                raise StandardError(em)
            LOG.debug("add info to db with successful. cobbler sysname: <{0}>".format(data_obj.cobbler_sysname))
            return True, 200
        except Exception as e:
            em = "Error happen with create physical!!!!! Rollback...msg: <{0}>".format(e)
            LOG.exception(em)
            MachineOperation.phy_rollback(data_obj)
            return False, 500

    @staticmethod
    def delete_physical(data_obj):
        try:
            # delete port from OpenStack
            ret = OpenStackHandle.delete_port(data_obj.tenant_token, data_obj.tenant_port_id)
            if not ret[0]:
                em = "delete port error. port id: <{0}>".format(data_obj.tenant_port_id)
                LOG.exception(em)
            LOG.debug("delete port from OpenStack with successful. port id: <{0}>".format(data_obj.tenant_port_id))

            # delete sdn vteps mapping
            ret = SDNSwitchConfig.sw_delete_vtep(data_obj.sw_sdn_ips,
                                                 data_obj.tenant_network_id,
                                                 data_obj.sw_sdn_passowrd,
                                                 data_obj.sw_sdn_username,
                                                 data_obj.tenant_token.strip()
                                                 )
            if not ret[0]:
                em = "config sdn switch error. switch ip: <{0}>".format(data_obj.sw_sdn_ips)
                LOG.exception(em)
                return False, ret[1]
            LOG.debug("delete vteps from sdn switch with successful. switch ip: <{0}>".format(data_obj.sw_sdn_ips))

            # set l2 switch port to access 4094
            ret = L2SwitchConfig.sw_delete_port(data_obj.tenant_network_id,
                                                data_obj.sw_l2_ip,
                                                data_obj.sw_l2_password,
                                                data_obj.sw_l2_username,
                                                data_obj.tenant_token.strip(),
                                                data_obj.sw_l2_port
                                                )
            if not ret[0]:
                em = "config l2 switch error. switch ip: <{0}> switch port: <{1}>".format(data_obj.sw_l2_ip, data_obj.sw_l2_port)
                LOG.exception(em)
                return False, ret[1]
            LOG.debug("config l2 switch with successful. l2 switch ip: <{0}>".format(data_obj.sw_l2_ip))

            # delete cobbler system name
            cb_obj = CobblerOperation()
            ret = cb_obj.remove_cobbler_system(data_obj.cobbler_sysname)
            if not ret[0]:
                em = "delete cobbler system error. system name: <{0}>".format(data_obj.cobbler_sysname)
                LOG.exception(em)
            LOG.debug("delete cobbler system with successful. cobbler system name: <{0}>".format(data_obj.cobbler_sysname))
            # delete db recorde
            ret = PhysicalTable.delete_by_userid_sysname(data_obj.tenant_user_id, data_obj.cobbler_sysname)
            if not ret:
                em = "delete physical info from db error. user id: <{0}>. cobbler system name: <{1}>".format(data_obj.tenant_user_id,
                                                                                                             data_obj.cobbler_sysname)
                LOG.exception(em)
                return False, 500
            LOG.debug("delete physical info from db with successful. cobbler system name: <{0}>".format(data_obj.cobbler_sysname))
            # update physical machine's status in cmdb
            ret = CMDBHandle.update_physical_status(data_obj.cmdb_uuid, u"可用")
            if not ret[0]:
                em = "error update cmdb's status.cmdb uuid: <{0}>".format(data_obj.cmdb_uuid)
                LOG.exception(em)
                return False, ret[1]
            LOG.debug("update cmdb's status with successful. cmdb uuid: <{0}>".format(data_obj.cmdb_uuid))
            return True, 200
        except Exception as e:
            em = "delete physical info error. cobbler system name: <{0}>. user id: <{1}>. msg: <{2}>".format(data_obj.cobbler_sysname,
                                                                                                             data_obj.tenant_user_id,
                                                                                                             e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def get_physicals(user_id, cobbler_sysname=None):
        try:
            return True, PhysicalTable.get_by_user_id(user_id)
        except Exception as e:
            em = "get physical error. msg: <{0}>".format(e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def update_host_status(user_id, cobbler_sysname, **kwargs):
        try:
            # update server status
            ret = PhysicalTable.update_by_userid_sysname(user_id, cobbler_sysname, kwargs)
            if not ret:
                em = "update cobbler system error. cobbler system name: <{0}>".format(cobbler_sysname)
                LOG.exception(em)
                return False, 500
            return True, 200
        except Exception as e:
            em = "update host status error. cobbler system name: <{0}>. user id: <{1}>. msg: <{2}>".format(user_id,
                                                                                                           cobbler_sysname,
                                                                                                           e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def host_charging(user_id, cobbler_sysname, token, user_name, resource_type="1_pm", used=1, order_type=2):
        try:
            ret = PhysicalTable.select_by_userid_sysname(user_id, cobbler_sysname)
            if not ret:
                em = "can not found cobbler system name: <{0}> with user id: <{1}>".format(cobbler_sysname, user_id)
                LOG.exception(em)
                return False, 400
            resource_id = ret.id
            timestamp = time.strftime("%Y-%m-%d %H:%M:%s", time.localtime())
            # charging
            data = {"timestamp": timestamp,
                    "resources": {resource_type: used,
                                  },
                    "resource_id": resource_id,
                    "tenant_id": user_id,
                    "_context_project_name": user_name,
                    "_context_user_name": user_name,
                    "resource": "physical machine",
                    "user_id": user_id,
                    "order_type": order_type,
                    }
            data = json.dumps(data)
            headers = {'X-Auth-Token': token.strip(),
                       'Content-type': 'application/json'}
            ret = post_http(url=options.charging_ep, data=data, headers=headers)
            if ret.status_code != 200:
                em = "charging error. system name: <{0}>  user id: <{1}>".format(cobbler_sysname, user_id)
                LOG.exception(em)
                return False, ret.status_code
            LOG.debug("host charging with successful. system name: <{0}>".format(cobbler_sysname))
            return True, 200
        except Exception as e:
            em = "host charging error. cobbler system name: <{0}>. user id: <{1}>. msg: <{2}>".format(cobbler_sysname,
                                                                                                      user_id,
                                                                                                      e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def phy_rollback(data_obj):
        """创建物理机失败后回滚操作"""
        # delete OpenStack port
        try:
            ret = OpenStackHandle.delete_port(data_obj.tenant_token, data_obj.tenant_port_id)
            if ret[0]:
                LOG.debug("delete port from OpenStack with successful. port ip: <{0}>".format(data_obj.tenant_port_id))
            if not ret[0]:
                em = "delete port error. port id: <{0}>".format(data_obj.tenant_port_id)
                LOG.exception(em)
        except Exception as e:
            LOG.exception("delete port from OpenStack with successful. port ip: <{0}> msg: <{0}>".format(data_obj.tenant_port_id,
                                                                                                         e))

        # delete cobbler system name
        try:
            cb_obj = CobblerOperation()
            ret = cb_obj.remove_cobbler_system(data_obj.cobbler_sysname)
            if ret[0]:
                LOG.debug("delete cobbler system with successful. cobbler system name: <{0}>".format(data_obj.cobbler_sysname))
            if not ret[0]:
                LOG.exception("delete cobbler system with failure. cobbler system name: <{0}>".format(data_obj.cobbler_sysname,))
        except Exception as e:
            em = "delete cobbler system error. system name: <{0}>. msg: <{1}>".format(data_obj.cobbler_sysname, e)
            LOG.exception(em)

        # delete db recorde
        try:
            ret = PhysicalTable.delete_by_userid_sysname(data_obj.tenant_user_id, data_obj.cobbler_sysname)
            if ret:
                LOG.debug("delete physical info from db with successful. cobbler system name: <{0}>".format(
                    data_obj.cobbler_sysname))
            if not ret[0]:
                LOG.exception("delete physical info from db with failure. cobbler system name: <{0}>".format(
                    data_obj.cobbler_sysname))
        except Exception as e:
            em = "delete physical info from db error. user id: <{0}>. cobbler system name: <{1}>. msg: <{2}>".format(
                data_obj.tenant_user_id,
                data_obj.cobbler_sysname,
                e)
            LOG.exception(em)

        # update physical machine's status in cmdb
        try:
            ret = CMDBHandle.update_physical_status(data_obj.cmdb_uuid, u"可用")
            if ret[0]:
                LOG.debug("update cmdb's status with successful. cmdb uuid: <{0}>".format(data_obj.cmdb_uuid))
            if not ret[0]:
                LOG.exception("update cmdb's status with failure. cmdb uuid: <{0}>".format(data_obj.cmdb_uuid))
        except Exception as e:
            em = "error update cmdb's status.cmdb uuid: <{0}>. msg: <{1}>".format(data_obj.cmdb_uuid, e)
            LOG.exception(em)


class CmdbData(object):
    def __init__(self, data):
        self.cobbler_ip = data.get("cobbler_ip")
        # self.cobbler_password = data.get("cobbler_password")
        self.cobbler_mask = data.get("cobbler_mask")
        self.cobbler_mac = data.get("cobbler_mac")
        self.cobbler_sysname = data.get("cobbler_sysname")
        # self.cobbler_sysname = data.get("cobbler_profile")
        self.cobbler_profile = data.get("cobbler_profile")
        self.tenant_mac = data.get("tenant_mac")
        self.tenant_port_id = data.get("tenant_port_id")
        # self.tenant_ip = data.get("tenant_ip")
        self.tenant_hostname = (data.get("tenant_hostname") if data.get("tenant_hostname") else "xy_cloud")
        self.tenant_mask = (str(IP(data.get("cidr")).netmask()) if data.get("cidr") else "")
        self.tenant_gateway = data.get("gateway", "")
        self.tenant_token = data.get("tenant_token")
        self.tenant_user_id = data.get("tenant_user_id")
        self.tenant_user_name = data.get("tenant_user_name")
        self.tenant_sys_password = data.get("tenant_sys_password")
        self.network_uuid = data.get("network_uuid")
        self.tenant_network_id = data.get("network_id")
        self.tenant_subnet_id = data.get("subnet_id")
        self.tenant_project_id = data.get("tenant_project_id")
        self.ipmi_ip = data.get("ipmi_ip")
        self.ipmi_username = data.get("ipmi_username")
        self.ipmi_password = data.get("ipmi_password")
        self.sw_l2_ip = data.get("sw_l2_ip")
        self.sw_l2_username = data.get("sw_l2_username")
        self.sw_l2_password = data.get("sw_l2_password")
        self.sw_l2_port = data.get("sw_l2_port")
        self.sw_sdn_ips = (data.get("sw_sdn_ips").split(",") if data.get("sw_sdn_ips") else "")
        self.sw_sdn_username = data.get("sw_sdn_username")
        self.sw_sdn_passowrd = data.get("sw_sdn_passowrd")
        self.cmdb_uuid = data.get("cmdb_uuid")
        self.physical_id = str(uuid.uuid1())
