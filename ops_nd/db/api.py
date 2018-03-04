#encoding=utf-8

from ops_nd.db.db import *
import ops_nd.log as logging

LOG = logging.getLogger(__name__)


class PhysicalTable(object):
    """table: physical_machine"""
    @staticmethod
    def select_by_userid_sysname(user_id, sysname, deleted=False):
        try:
            return P_machine_get_by_userid_(user_id, sysname, deleted=deleted)
        except Exception as e:
            em = "get user info error. user id: <{0}>. sysname: <{1}>. msg: <{2}>".format(user_id, sysname, e)
            LOG.exception(em)
            return False

    @staticmethod
    def select_all():
        try:
            return P_machine_list()
        except Exception as e:
            em = "get user info error. msg: <{0}>".format(e)
            LOG.exception(em)
            return False

    @staticmethod
    def update_by_userid_sysname(user_id, cb_sysname, values):
        try:
            P_machine_update(user_id, cb_sysname, values)
            return True
        except Exception as e:
            em = "update user info error. msg: <{0}>".format(e)
            LOG.exception(em)
            return False


    @staticmethod
    def delete_by_userid_sysname(user_id, cb_sysname):
        try:
            P_machine_delete(user_id, cb_sysname)
            return True
        except Exception as e:
            em = "delete user info error. msg: <{0}>".format(e)
            LOG.exception(em)
            return False

    @staticmethod
    def add_data(values):
        try:
            P_machine_create(values)
            return True
        except Exception as e:
            em = "add user info error. msg: <{0}>".format(e)
            LOG.exception(em)
            return False

    @staticmethod
    def get_by_cmdbid(uuid):
        try:
            return P_machine_get_by_cmdbID(uuid)
        except Exception as e:
            em = "get user info error. cmdbid: <{0}>. msg: <{0}>".format(uuid, e)
            LOG.exception(em)
            return False

    @staticmethod
    def get_by_id(id):
        try:
            return P_machine_get_by_id(id)
        except Exception as e:
            em = "get user info error. id: <{0}>. msg: <{1}>".format(id,e)
            LOG.exception(em)
            return False

    @staticmethod
    def get_undelet():
        try:
            return P_machine_get_undelete()
        except Exception as e:
            em = "get user info error. id: <{0}>. msg: <{1}>".format(id,e)
            LOG.exception(em)
            return False

    @staticmethod
    def get_by_user_id(user_id):
        try:
            return P_machine_get_by_user_id(user_id)
        except Exception as e:
            em = "get user info error. id: <{0}>. msg: <{1}>".format(id,e)
            LOG.exception(em)
            return False
