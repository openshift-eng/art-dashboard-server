import os
import boto3
from .constants import AWSConfigurationConstants as awscc
import threading


def singleton(cls):
    instance = [None]

    def wrapper(*args, **kwargs):
        if instance[0] is None:
            instance[0] = cls(*args, **kwargs)
        return instance[0]

    return wrapper


@singleton
class SimpleDBClientManagerPool(object):

    """
    Pools client object for sdb.

    Refer:
    https://sourcemaking.com/design_patterns/object_pool/python/1
    """

    def __init__(self, size=10):
        self._size = size
        self._pool = [SimpleDBClientManager() for _ in range(self._size)]
        self._lock = threading.Lock()

    def acquire(self):
        self._lock.acquire()
        client_manager = self._pool.pop()
        self._lock.release()
        return client_manager

    def release(self, client_manager):
        self._lock.acquire()
        self._pool.append(client_manager)
        self._lock.release()


class SimpleDBClientManager(object):

    """
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sdb.html#SimpleDB.Client.select
    http://boto.cloudhackers.com/en/latest/simpledb_tut.html
    """

    def __init__(self):

        # should not be here check for config param present
        # if awscc.AWS_PROFILE in os.environ and awscc.AWS_DEFAULT_REGION in os.environ:
        self._client = boto3.client("sdb", region_name=os.environ[awscc.AWS_DEFAULT_REGION])
        self._domain = os.environ[awscc.SDB_DOMAIN]

    @staticmethod
    def handle_where(where_string_recv):
        where_string = ""

        if where_string_recv == "":
            where_string += "where `build.time.unix` is not null"
        else:
            where_string = "where `build.time.unix` is not null and " + where_string_recv

        return where_string

    def run_select(self, data: dict) -> dict:

        where = SimpleDBClientManager.handle_where(data['where'])

        if "next_token" in data:
            next_token = data["next_token"]
        else:
            next_token = ""

        order_by = "order by `build.time.unix` desc"

        try:

            if next_token == "":
                select_response = self._client.select(
                    SelectExpression="select * from {} {} {} limit {}".
                    format(self._domain, where, order_by, data['limit']),
                    NextToken=next_token,
                    ConsistentRead=False
                )
            else:
                select_response = self._client.select(
                    SelectExpression="select * from {} {} {} limit {}".format(self._domain, where, order_by, data['limit']),
                    NextToken=next_token
                )
            return select_response
        except Exception as e:
            return {"error": "There is something wrong with the filter backend query. We'll"
                             " fix it soon. If it's an API call from another application most probably"
                             " you're doing something wrong with the syntax.",
                    "exception": str(e)}
