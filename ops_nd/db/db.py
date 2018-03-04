from ops_nd.db.session import model_query, get_session
from ops_nd import exception

from ops_nd.db.models import *


def service_get_by_args(host, binary):
    return model_query(service_models.Service). \
        filter_by(host=host). \
        filter_by(binary=binary). \
        first()


def service_create(values):
    service_ref = Service()
    service_ref.update(values)
    service_ref.save()
    return service_ref


def service_list():
    return model_query(Service).all()


def service_get(service_id, session=None):
    result = model_query(Service, session=session). \
        filter_by(id=service_id). \
        first()
    if not result:
        raise exception.ServiceNotFound(service_id=service_id)
    return result


def service_update(service_id, values):
    session = get_session()
    with session.begin():
        service_ref = service_get(service_id, session=session)
        service_ref.update(values)
        service_ref.save(session=session)


def P_machine_get_by_userid_(user_id, cb_sysname, deleted=False, session=None):
    return model_query(PhysicalMachine, session=session). \
        filter_by(user_id=user_id). \
        filter_by(cobbler_sysname=cb_sysname). \
        filter_by(deleted=deleted). \
        first()


def P_machine_create(values):
    P_machine_ref = PhysicalMachine()
    P_machine_ref.update(values)
    P_machine_ref.save()
    return P_machine_ref


def P_machine_list():
    return model_query(PhysicalMachine).all()


def P_machine_update(user_id, cb_sysname, values):
    session = get_session()
    with session.begin():
        P_machine_ref = P_machine_get_by_userid_(user_id, cb_sysname, session=session)
        P_machine_ref.update(values)
        P_machine_ref.save(session=session)


def P_machine_delete(user_id, cb_sysname):
    session = get_session()
    with session.begin():
        P_machine_ref = P_machine_get_by_userid_(user_id, cb_sysname, session=session)
        if P_machine_ref:
            P_machine_ref.delete(session=session)


def P_machine_get_by_cmdbID(cmdb_id, deleted=False, session=None):
    return model_query(PhysicalMachine, session=session). \
        filter_by(cmdb_uuid=cmdb_id). \
        filter_by(deleted=deleted). \
        first()


def P_machine_get_by_id(id, deleted=False, session=None):
    return model_query(PhysicalMachine, session=session). \
        filter_by(id=id). \
        filter_by(deleted=deleted). \
        first()


def P_machine_get_undelete(deleted=False, session=None):
    return model_query(PhysicalMachine, session=session). \
        filter_by(deleted=deleted). \
        all()


def P_machine_get_by_user_id(user_id, deleted=False, session=None):
    return model_query(PhysicalMachine, session=session). \
        filter_by(user_id=user_id). \
        filter_by(deleted=deleted). \
        all()
