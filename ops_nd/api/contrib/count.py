import tornado.web
import json


from ops_nd.api.auth import auth
from ops_nd.service import db
from ops_nd import log as logging

from ops_nd.db.session import query_result_json

LOG = logging.getLogger(__name__)
url_map = {
            r"/count$": 'count',
        }

class count(auth.BaseAuth):
    def get(self):
        counts = query_result_json(db.count_list())
        self.write(counts)
