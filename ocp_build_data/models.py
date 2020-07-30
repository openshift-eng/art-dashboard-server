from django.db import models, transaction


# Create your models here.
class OpenShiftCurrentAdvisoryManager(models.Manager):

    def get_advisories_for_branch(self, branch_name):
        version_rows = self.filter(openshift_version=branch_name).values()
        return_response = {"current": {}, "previous": {}}

        for row in version_rows:
            return_response["current"][row["advisory_type"]] = row["current_advisory_id"]
            return_response["previous"][row["advisory_type"]] = row["previous_advisory_id"]

        return return_response

    @transaction.atomic
    def delete_old_entries_and_create_new(self, branch_name, current_advisories, previous_advisories,
                                          current_sha, previous_sha):

        self.filter(openshift_version=branch_name).delete()
        delete_all_branch_entries = transaction.savepoint()

        new_entries = []

        for advisory_type in current_advisories:
            new_entry = OpenShiftCurrentAdvisory(openshift_version=branch_name,
                                                 advisory_type=advisory_type,
                                                 current_advisory_id=current_advisories[advisory_type],
                                                 previous_advisory_id=previous_advisories[advisory_type],
                                                 current_advisory_sha=current_sha,
                                                 previous_advisory_sha=previous_sha)
            new_entries.append(new_entry)

        try:
            for entry in new_entries:
                entry.save()
            else:
                transaction.savepoint_commit(delete_all_branch_entries)
        except Exception as e:
            transaction.savepoint_rollback(delete_all_branch_entries)

    def check_if_current_advisories_match(self, branch_name, advisories):

        for advisory_type in advisories:
            q_s = self.filter(openshift_version=branch_name, current_advisory_id=str(advisories[advisory_type]))
            q_s_count = 0
            for _ in q_s:
                q_s_count += 1

            if q_s_count == 0:
                break
        else:
            # if the loop never breaks, that means all the ids for each advisory
            # type match and hence no need for backward lookup
            return True

        return False


class OpenShiftCurrentAdvisory(models.Model):

    class Meta:
        db_table = "log_openshift_release_advisory"

    log_openshift_release_advisory_id = models.AutoField(primary_key=True)
    openshift_version = models.CharField(max_length=50, null=False, blank=False)
    advisory_type = models.CharField(max_length=100, null=False, blank=False)
    current_advisory_id = models.CharField(max_length=20, null=False, blank=False)
    previous_advisory_id = models.CharField(max_length=20, null=False, blank=False)
    current_advisory_sha = models.CharField(max_length=200, null=False, blank=False, default="")
    previous_advisory_sha = models.CharField(max_length=200, null=False, blank=False, default="")
    objects = OpenShiftCurrentAdvisoryManager()
