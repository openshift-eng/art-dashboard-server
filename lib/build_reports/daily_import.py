from lib.aws.sdb import SimpleDBClientManagerPool
import lib.build_reports.constants as build_report_constants

requests = []


def get_required_data(filter_data):
    start = True
    next_token = None

    if "limit" not in filter_data:
        filter_data["limit"] = 100

    if "where" not in filter_data:
        return []

    if "next_token" in filter_data:
        del filter_data["next_token"]

    pool_manager = SimpleDBClientManagerPool()
    client_manager = pool_manager.acquire()

    while next_token or start:

        select_response = client_manager.run_select(filter_data)

        if start:
            start = False

        yield select_response

        if "NextToken" in select_response:
            next_token = select_response["NextToken"]
            filter_data["next_token"] = next_token
        else:
            next_token = None
            del filter_data["next_token"]

    pool_manager.release(client_manager)


def generate_sdb_request(where, limit=None):

    if not limit:
        limit = 100

    request = {
        "where": where,
        "limit": limit
    }

    return request


def parse_batched_data(batched_data, request_id):

    final_data = []

    for batch_data in batched_data:
        if "Items" in batch_data:
            items = batch_data["Items"]
            for item in items:
                attributes = item["Attributes"]
                data_point = {}
                for attribute in attributes:
                    if attribute["Name"] in build_report_constants.BUILD_TABLE_COLUMN:
                        if attribute["Value"] == "":
                            attribute["Value"] = None
                        data_point[build_report_constants.BUILD_TABLE_COLUMN[attribute["Name"]]] = attribute["Value"]
                data_point["request_id"] = request_id
                final_data.append(data_point)
    return final_data


def generate_where_condition_daily_import(date):
    return "`build.time.iso` like \"{}%\"".format(date)


def import_daily_data(date, request_id):
    sdb_request = generate_sdb_request(generate_where_condition_daily_import(date))
    batched_data = get_required_data(sdb_request)
    final_data = parse_batched_data(batched_data, request_id)
    return final_data
