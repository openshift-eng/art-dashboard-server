import time
import schedule
import datetime
import threading
from build_health.serializers import ImportBuildViewSerializer, DailyReportViewSerializer
from build_health.models import HealthRequests, Build


def import_data_from_sdb_to_mysql():
    yesterdays_date = datetime.datetime.now().date() - datetime.timedelta(days=1)

    mysql_import_request = {
        "date": yesterdays_date
    }

    daily_build_summary_request = {
        "start": yesterdays_date,
        "end": yesterdays_date
    }

    daily_import_serializer = ImportBuildViewSerializer(data=mysql_import_request)
    if daily_import_serializer.is_valid():
        status, message = HealthRequests.objects.if_daily_import_request_already_satisfied(daily_import_serializer.data["date"])
        import_return = {"status": status, "message": message}
    else:
        import_return = {"status": "error", "message": daily_import_serializer.errors}

    if import_return["status"]:

        daily_build_summary_serializer = DailyReportViewSerializer(data=daily_build_summary_request)

        if daily_build_summary_serializer.is_valid():
            request = daily_build_summary_serializer.data
            request["type"] = "daily"
            request_status = HealthRequests.objects.is_request_already_satisfied(request)

            if not request_status:
                message, status, request_id = HealthRequests.objects.handle_build_health_request(request)

                if Build.objects.generate_daily_report(daily_build_summary_serializer.data["start"], request_id):
                    import_return["daily_build_summary"] = {"status": "success", "message": "Daily report generated."}
                else:
                    import_return["daily_build_summary"] = {"status": "error", "message": "Something went wrong."}
            else:
                import_return["daily_build_summary"] = {"status": "error", "message": "Request already completed."}
        else:
            import_return["daily_build_summary"] = {"status": "error", "message": daily_build_summary_serializer.errors}

        print(import_return)


def add_to_schedule():
    schedule.every().day.at("08:00").do(import_data_from_sdb_to_mysql)


def run_scheduler():
    add_to_schedule()
    while 1:
        print("Running cron schedules.")
        schedule.run_pending()
        time.sleep(600)


def start_scheduler_thread():

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
