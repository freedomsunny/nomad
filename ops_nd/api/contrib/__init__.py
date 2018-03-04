#coding=utf8

from ops_nd.api.utils import load_url_map
from ops_nd import log as logging

LOG = logging.getLogger('api')

url_map = load_url_map(__path__, __package__, log=LOG)
