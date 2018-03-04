import tornado.web
import json
import uuid

from ops_nd.api.auth import auth
from ops_nd.service import db
from ops_nd import log as logging
from ops_nd.db.session import query_result_json
from ops_nd import log as logging
from ops_nd.api.auth.auth import Base, BaseAuth
from ops_nd.plugins.machine_handle import MachineOperation
from ops_nd.plugins.machine_handle import CmdbData
from ops_nd.db.api import *
from ops_nd.plugins.cobbler_handle import CobblerOperation
from ops_nd.db.session import query_result_json
from ops_nd.plugins.openstack_handle import OpenStackHandle
from ops_nd.plugins.cmdb_handle import CMDBHandle
from ops_nd.plugins.virtual_and_physical import VPHandle

LOG = logging.getLogger(__name__)

url_map = {
    r"/helloworld$": 'helloworld',
    r"/physical/create$": "Physical",
    r"/physical/get$": "Physical",
    r"/physical/delete$": "Physical",
    r"/profile/get$": "Profiles",
    r"/physical/finish$": "HostFinish",
    r"/physical/getphy": "GetPhysicalFromCMDB",
}


class helloworld(BaseAuth):
    def get(self):
        self.write("Hello World! I love this world!")
        LOG.debug('hello world is request')


class Physical(BaseAuth):

    def get(self):
        try:
            user_id = self.context.get("user_id")
            ret = MachineOperation.get_physicals(user_id)
            if not ret[0]:
                self.set_status(ret[1])
            else:
                self.write(query_result_json(self.context, ret[1]))
        except Exception as e:
            em = "Get Physicals error. msg: <{0}>".format(e)
            LOG.exception(em)
            self.set_status(500)

    def post(self):
        try:
            data = json.loads(self.request.body)
            cmdb_uuid = data.get("cmdb_uuid")
            network_uuid = data.get("network_uuid")
            cmdb_data = CMDBHandle.get_physical_info(cmdb_uuid)
            network_data = VPHandle.get_network_info(network_uuid, self.context.get("token"))
            data.update(cmdb_data)
            data.update(network_data)
            data["tenant_user_id"] = self.context.get("user_id")
            data["tenant_user_name"] = self.context.get("user").get("user").get("name")
            data["tenant_token"] = self.context.get("token")
            data["tenant_project_id"] = self.context.get("tenant_id")
            data_obj = CmdbData(data)
            ret = MachineOperation.create_physical(data_obj)
            if not ret[0]:
                self.set_status(ret[1])
        except Exception as e:
            em = "create physical error. msg: <{0}>".format(e)
            LOG.exception(em)
            self.set_status(500)

    def delete(self):
        try:
            physical_id = self.get_argument('uuid', None)
            if not physical_id:
                self.set_status(400)
                return
            p_ret = PhysicalTable.get_by_id(physical_id)
            if not p_ret:
                self.set_status(500)
                return
            cmdb_uuid = p_ret.cmdb_uuid
            network_uuid = p_ret.network_uuid
            data = {}
            data["tenant_user_id"] = self.context.get("user_id")
            data["tenant_user_name"] = self.context.get("user").get("user").get("name")
            data["tenant_token"] = self.context.get("token")
            data["tenant_port_id"] = p_ret.tenant_port_id
            data["cobbler_sysname"] = p_ret.cobbler_sysname
            data["cmdb_uuid"] = p_ret.cmdb_uuid
            cmdb_data = CMDBHandle.get_physical_info(cmdb_uuid)
            network_data = VPHandle.get_network_info(network_uuid, self.context.get("token"))
            data.update(cmdb_data)
            data.update(network_data)
            data_obj = CmdbData(data)
            # server charging
            if p_ret.status == "success":
                tenant_token = OpenStackHandle.get_token()
                if not tenant_token:
                    self.set_status(500)
                    return
                ret = MachineOperation.host_charging(data_obj.tenant_user_id,
                                                     data_obj.cobbler_sysname,
                                                     tenant_token,
                                                     data_obj.tenant_user_name,
                                                     used="")
                if not ret[0]:
                    em = "host charging error..."
                    LOG.exception(em)
                    self.set_status(ret[1])
            ret = MachineOperation.delete_physical(data_obj)
            if not ret[0]:
                self.set_status(ret[1])
        except Exception as e:
            em = "delete physical error. msg: <{0}>".format(e)
            LOG.exception(em)
            self.set_status(500)


class Profiles(BaseAuth):
    def get(self):
        try:
            cb_obj = CobblerOperation()
            ret = cb_obj.get_profiles()
            self.write(query_result_json(self.context, ret))
        except Exception as e:
            em = "get cobbler profiles error. msg: <{0}>".format(e)
            LOG.exception(em)
            self.set_status(500)


class HostFinish(Base):
    def post(self):
        """when host install finish. charging & update server status & configure l2 switch"""
        try:
            data = json.loads(self.request.body)
            if not data:
                em = "invalid args.."
                LOG.exception(em)
                self.set_status(400)
            physical_id = data.get("id")
            p_ret = PhysicalTable.get_by_id(physical_id)
            if not p_ret:
                em = "can not found any physical id by id: <{0}>".format(physical_id)
                LOG.exception(em)
                self.set_status(400)
            cobbler_sysname = p_ret.cobbler_sysname
            tenant_user_id = p_ret.user_id
            tenant_user_name = p_ret.user_name
            cmdb_uuid = p_ret.cmdb_uuid
            tenant_token = OpenStackHandle.get_token()
            # update server's status
            ret = MachineOperation.update_host_status(tenant_user_id, cobbler_sysname, status="success")
            if not ret[0]:
                em = "host finish error..."
                LOG.exception(em)
                self.set_status(ret[1])
            LOG.debug("update host's status with successful. cobbler_sysname: <{0}>".format(cobbler_sysname))
            # server charging
            ret = MachineOperation.host_charging(tenant_user_id, cobbler_sysname, tenant_token, tenant_user_name)
            if not ret[0]:
                em = "host charging error..."
                LOG.exception(em)
                self.set_status(ret[1])
            LOG.debug("server charging with successful. cobbler_sysname: <{0}>".format(cobbler_sysname))
            # set cobbler sw port to 4094 vlan

            LOG.debug("port port vlan to 4094 with successful. cobbler_sysname: <{0}>".format(cobbler_sysname))
        except Exception as e:
            em = "charging error with user id: <{0}>".format(e)
            LOG.exception(em)
            self.set_status(500)


class GetPhysicalFromCMDB(Base):
    def get(self):
        try:
            ret = CMDBHandle.get_physical_machine()
            if not ret[0]:
                self.set_satus(500)
            self.write(ret[1])
        except Exception as e:
            em = "get physical from cmdb error. msg: <{0}>".format(e)
            LOG.exception(em)
            self.set_status(500)
