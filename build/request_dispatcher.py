from build_health.models import Build


def handle_build_post_request(request_params):

    request_params = dict(request_params)

    order_by = None
    order_by_string = ""
    where = None
    where_string = ""
    query_string = ""

    if "order" in request_params:
        order_by = request_params["order"]
        del request_params["order"]

        if len(order_by) != 0 and len(order_by) == 2:
            if "sort_filter_column" in order_by and "sort_filter_order" in order_by:
                order_by_string += " order by {} {}".format(order_by["sort_filter_column"], order_by["sort_filter_order"])
        else:
            order_by_string += " order by iso_time desc"

    else:
        order_by_string += " order by iso_time desc"

    for column in request_params:
        for column_condition in request_params[column]:
            print(column_condition)
            if "like_or_where" not in column_condition or \
                    "value" not in column_condition:
                return {"status": "error", "message": "Missing value \"like_or_where\" in query string.", "data": []}

            if column_condition["like_or_where"] == "where":
                value = str(column_condition["value"])
                value = value.replace("%", "%%")
                if "cond" in column_condition:
                    where_string += "{} {} \"{}\" and ".format(column, column_condition["cond"], value)
                else:
                    where_string += "{} = \"{}\" and ".format(column, value)
            elif column_condition["like_or_where"] == "like":
                value = str(column_condition["value"])
                value = value.replace("%", "\\%%")
                where_string += "{} like \"%%{}%%\" and ".format(column, value)

    if where_string == "":
        query_string = "select * from log_build " + order_by_string + " limit 200"
    else:
        where_string = "where " + where_string[:-4]
        query_string = "select * from log_build " + where_string + order_by_string

    print(query_string)

    result = Build.objects.generate_build_data_for_ui(query_string)
    return {"status": "success", "message": "Data is ready.", "data": result}
