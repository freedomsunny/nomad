# encoding=utf-8
import json

import ops_nd.log as logging
from ops_nd.options import get_options
from ops_nd.utils import get_http, post_http, put_http
from ops_nd.plugins.openstack_handle import OpenStackHandle

LOG = logging.getLogger(__name__)

cmdb_opts = [
]
options = get_options(cmdb_opts)


class CMDBHandle(object):
    @staticmethod
    def get_physical_info(cmdb_uuid):
        try:
            admin_token = OpenStackHandle.get_token()
            url = options.cmdb_ep + "/assets/" + cmdb_uuid
            headers = {'X-Auth-Token': admin_token.strip()}
            ret = get_http(url=url, headers=headers)
            if ret.status_code != 200:
                em = "get physical info from cmdb error...."
                LOG.exception(em)
                return False, ret.status_code
            return ret.json()["property"]
        except Exception as e:
            em = "get physical info from cmdb error. msg: <{0}>".format(e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def update_physical_status(cmdb_uuid, status):
        try:
            url = options.cmdb_ep + "/assets/" + cmdb_uuid
            data = {"property": {"status": status
                                 }
                    }
            admin_token = OpenStackHandle.get_token()
            if not admin_token:
                em = "can not update physical status. can not get admin token "
                LOG.exception(em)
                return False, 500
            headers = {'X-Auth-Token': admin_token.strip(), 'Content-type': 'application/json'}
            data = json.dumps(data)
            ret = put_http(url=url, data=data, headers=headers)
            if ret.status_code != 200:
                em = "update cmdb info error....cmdb uuid: <{0}>".format(cmdb_uuid)
                LOG.exception(em)
                return False, ret.status_code
            return True, 200
        except Exception as e:
            em = "update physical machine error. cmdb uuid: <{0}>. msg: <{1}>".format(cmdb_uuid, e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def get_physical_machine():
        try:
            data = []
            url = options.cmdb_ep + u"/assets?target=E@application:金属裸机andE@status:可用&type=server"
            admin_token = OpenStackHandle.get_token()
            if not admin_token:
                em = "ERROR can not get physical data. can not get admin token "
                LOG.exception(em)
                return False, 500
            headers = {'X-Auth-Token': admin_token.strip()}
            ret = get_http(url=url, headers=headers)
            res_data = ret.json()
            for s in res_data.get("data"):
                property = {"disk": s.get('property').get('disk', ""),
                            "cpu": s.get('property').get("cpu", ""),
                            "ram": s.get('property').get("ram", ""),
                            "server_model": s.get('property').get("server_model", ""),
                            }
                s["property"] = property
                data.append(s)
            res_data["data"] = data
            return True, res_data
        except Exception as e:
            em = "get physical machine from cmdb error. msg: <{0}>".format(e)
            LOG.exception(em)
            return False, 500
