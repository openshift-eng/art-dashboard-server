from django.db import models


class DailyBuildReportManager(models.Manager):

    def handle_request_for_daily_report_view_get(self, request_type, date=None):

        if request_type == "overview":
            daily_stats = self.raw("select 1 as log_build_daily_summary_id, date,sum( if(fault_code = 0, count,0)) as success, sum( if(fault_code != 0 OR fault_code is NULL, count, 0)) as failure, sum(count) as total, (sum( if(fault_code = 0, count,0))/sum(count))*100 as success_rate  from log_build_daily_summary group by 2 order by 2 desc")
            daily_stats_filters = []
            for daily_stat in daily_stats:
                d_stat = {"date": daily_stat.date,
                          "success": daily_stat.success,
                          "failure": daily_stat.failure,
                          "total": daily_stat.total,
                          "success_rate": daily_stat.success_rate}

                daily_stats_filters.append(d_stat)

            return daily_stats_filters

        elif request_type == "fordate":
            if date is None:
                return []
            else:
                date_wise_stats = self.raw("select 1 as log_build_daily_summary_id, date, label_name, sum( if(fault_code = 0, count,0)) as success, sum( if(fault_code != 0 OR fault_code is NULL, count, 0)) as failure, sum(count) as total, (sum( if(fault_code = 0,count,0))/sum(count))*100 as success_rate  from log_build_daily_summary where date=\"{0}\" group by 2,3 order by 7,6 desc".format(date))
                date_wise_stats_filtered = []
                total = success = failure = 0
                for date_wise_stat in date_wise_stats:
                    d_stat = {"date": date_wise_stat.date,
                              "success": date_wise_stat.success,
                              "failure": date_wise_stat.failure,
                              "total": date_wise_stat.total,
                              "success_rate": date_wise_stat.success_rate,
                              "label_name": date_wise_stat.label_name}

                    total += date_wise_stat.total
                    success += date_wise_stat.success
                    failure += date_wise_stat.failure

                    date_wise_stats_filtered.append(d_stat)

                if total != 0:
                    data = {
                        "total": total,
                        "success": success,
                        "failure": failure,
                        "success_rate": (success/total)*100,
                        "table_data": date_wise_stats_filtered
                    }
                else:
                    data = {
                        "total": total,
                        "success": success,
                        "failure": failure,
                        "success_rate": 100,
                        "table_data": date_wise_stats_filtered
                    }
                return data
        elif request_type == "datewise_fault_code_stats":
            if date is None:
                return []
            else:
                fault_code_wise_stats = self.raw("select 1 as log_build_daily_summary_id, case when fault_code = \"\" then \"unknown\" else fault_code end as fault_code,sum(count) as count from log_build_daily_summary where date=\"{0}\" group by 2".format(date))
                fault_code_wise_stats_filtered = []
                for fault_code_wise_stat in fault_code_wise_stats:
                    d_stat = {"fault_code": fault_code_wise_stat.fault_code,
                              "count": fault_code_wise_stat.count}
                    fault_code_wise_stats_filtered.append(d_stat)

                return fault_code_wise_stats_filtered
        else:
            return {"message": "Invalid request type."}


class BuildManager(models.Manager):

    def generate_build_data_for_ui(self, query_string):
        raw_results = self.raw(query_string)

        results = []

        for raw_result in raw_results:
            result = dict()
            result["build_id"] = raw_result.build_0_id
            result["fault_code"] = raw_result.brew_faultCode
            result["task_id"] = raw_result.brew_task_id
            result["iso_time"] = raw_result.build_time_iso
            result["group"] = raw_result.group
            result["label_name"] = raw_result.label_name
            result["jenkins_build_url"] = raw_result.jenkins_build_url
            result["nvr"] = raw_result.build_0_nvr
            result["build_source"] = raw_result.build_0_source
            result["dg_name"] = raw_result.dg_name
            result["build_commit_url_github"] = raw_result.label_io_openshift_build_commit_url
            result["jenkins_build_url"] = raw_result.jenkins_build_url
            result["jenkins_build_number"] = raw_result.jenkins_build_number
            result["jenkins_job_name"] = raw_result.jenkins_job_name
            result["build_name"] = raw_result.build_0_name
            result["build_version"] = raw_result.build_0_version
            result["dg_qualified_name"] = raw_result.dg_qualified_name
            result["label_version"] = raw_result.label_version
            result["dg_namespace"] = raw_result.dg_namespace
            result["dg_commit"] = raw_result.dg_commit
            results.append(result)

        return results

    def get_all_for_a_date_for_a_column(self, column_name, column_value, date):
        raw_results = self.raw(
            "select log_log_build_id, build_0_id, brew_faultCode, brew_task_id, build_time_iso, `group`, label_name, jenkins_build_url from log_build where date(build_time_iso) = \"{}\" and {}=\"{}\"".format(
                date, column_name, column_value))
        results = []
        for raw_result in raw_results:
            result = dict()
            result["build_id"] = raw_result.build_0_id
            result["fault_code"] = raw_result.brew_faultCode
            result["task_id"] = raw_result.brew_task_id
            result["iso_time"] = raw_result.build_time_iso
            result["group"] = raw_result.group
            result["label_name"] = raw_result.label_name
            result["jenkins_build_url"] = raw_result.jenkins_build_url
            results.append(result)
        return results

    def get_all_for_a_date(self,date):

        raw_results = self.raw("select log_log_build_id, build_0_id, brew_faultCode, brew_task_id, build_time_iso, `group`, label_name jenkins_build_url from log_build where date(build_time_iso) = \"{}\"".format(date))
        results = []
        for raw_result in raw_results:
            result = dict()
            result["build_id"] = raw_result.build_0_id
            result["fault_code"] = raw_result.brew_faultCode
            result["task_id"] = raw_result.brew_task_id
            result["iso_time"] = raw_result.build_time_iso
            result["group"] = raw_result.group
            result["label_name"] = raw_result.label_name
            result["jenkins_build_url"] = raw_result.jenkins_build_url
            results.append(result)
        return results
