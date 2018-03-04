# encoding=utf-8
import json

import ops_nd.log as logging
from ops_nd.options import get_options
from ops_nd.utils import get_http, post_http, delete_http
from ops_nd import cache

LOG = logging.getLogger(__name__)

ovs_opts = [
]
options = get_options(ovs_opts)


class OpenStackHandle(object):
    @staticmethod
    def apply_port(tenant_id, network_id, subnet_id, mac_address):
        """
        method to get network's ip address from openstack 
        :param token: 
        :param network_id: 
        :param subnet_id: 
        :return: 
        """
        try:
            url = '{0}/ports'.format(options.neutron_endpoint)

            if not network_id or not subnet_id or not mac_address:
                em = "invalid parameter network_id or subnet_id  or mac address"
                LOG.exception(em)
                return False, 400
            # get admin token
            token = OpenStackHandle.get_token()
            if not token:
                em = "get admin token error....."
                LOG.exception(em)
                return False, 400
            bind_host = options.overlay_ip.replace(".", "-")
            #
            # data = {"port": {"network_id": network_id,
            #                  "fixed_ips": [{"subnet_id": subnet_id}],
            #                  "mac_address": mac_address,
            #                  "device_owner": "neutron:compute:nova"
            #                  }
            #         }

            data = {"port": {"network_id": network_id,
                             "tenant_id": tenant_id,
                             "fixed_ips": [{"subnet_id": subnet_id,
                                            }
                                           ],
                             "mac_address": mac_address,
                             "binding:host_id": bind_host,
                             "device_owner": "compute:nova"
                             }
                    }
            data = json.dumps(data)
            if not token:
                em = "invalid parameter token"
                LOG.exception(em)
                return False, 500
            header = {'Content-type': 'application/json', 'X-Auth-Token': token.strip()}
            ret = post_http(url=url, data=data, headers=header)
            # check is it error
            if ret.status_code != 201:
                em = "openstack error.assign ip address from openstack error. network id: <{0}>  subnet_id: <{1}> msg: <{2}>".format(network_id,
                                                                                                                                     subnet_id,
                                                                                                                                     ret.json())
                LOG.exception(em)
                return False, ret.status_code
            return True, ret.json()
        except Exception as e:
            em = "apply port from OpenStack error. network id: <{0}> subnet_id: <1>. msg: <{2}>".format(network_id,
                                                                                                        subnet_id, e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def delete_port(token, port_id):
        if not token or not port_id:
            em = "token or port_id is invalid"
            LOG.exception(em)
            return False, 400
        header = {'X-Auth-Token': token.strip()}
        url = "{0}/ports/{1}".format(options.neutron_endpoint,
                                     port_id.strip())
        ret = delete_http(url=url, headers=header)
        # check is it error
        if ret.status_code != 204:
            em = "error delete port with id :{0}".format(port_id)
            LOG.exception(em)
            return False, ret.status_code
        return True, 200

    @staticmethod
    def get_token(username=options.username, password=options.password, tenant=options.tenant):
        backend = cache.Backend()
        if tenant:
            token = backend.get("keystone_tenant_endpoint")
            if not token:
                data = {"auth":
                            {"passwordCredentials":
                                 {"username": username,
                                  "password": password},
                             'tenantName': tenant
                             },
                        }
                r = post_http(method='post', url='%s/tokens' % options.keystone_admin_endpoint,
                              data=json.dumps(data))
                if r.status_code == 200 and r.json().get('access', ''):
                    token = r.json().get('access').get("token").get("id")
                    backend.set("keystone_tenant_endpoint", token)
                    return r.json()['access']['token']['id']
                else:
                    return False
            return token
        else:
            token = backend.get("keystone_admin_endpoint")
            if not token:
                data = {"auth":
                            {"passwordCredentials":
                                 {"username": options.username,
                                  "password": options.password
                                  },
                             "tenantName": options.tenant}
                        }
                try:
                    # first get token from redis. if not get from keystone
                    r = post_http(method='post', url='%s/tokens' % options.keystone_admin_endpoint,
                                  data=json.dumps(data))
                    data = r.json()
                    if r.status_code == 200 and data.get("access"):
                        token = data.get('access').get("token").get("id")
                        if not token:
                            em = "can not get admin token"
                            LOG.exception(em)
                            return False
                        backend.set("keystone_admin_endpoint", token)
                        return token
                    else:
                        return False
                except Exception as e:
                    LOG.exception(e)
                    return False
            return token
