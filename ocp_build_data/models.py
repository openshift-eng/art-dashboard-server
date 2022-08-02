from django.db import models, transaction


# Create your models here.
class OpenShiftCurrentAdvisoryManager(models.Manager):

    @transaction.atomic
    def delete_old_entries_and_create_new(self, branch_name, advisories):
        self.filter(openshift_version=branch_name).delete()
        delete_all_branch_entries = transaction.savepoint()

        brew_event = advisories[0][0]
        entry = OpenShiftCurrentAdvisory(openshift_version=branch_name, brew_event=str(brew_event))

        try:
            if entry:
                entry.save()
            else:
                transaction.savepoint_commit(delete_all_branch_entries)
        except Exception as e:
            transaction.savepoint_rollback(delete_all_branch_entries)

    def check_if_current_advisories_match(self, branch_name, advisories):
        brew_event = str(advisories[0][0])
        database_brew_event = self.filter(openshift_version=branch_name, brew_event=str(brew_event))
        if not database_brew_event:
            return False
        return True


class OpenShiftCurrentAdvisory(models.Model):
    class Meta:
        db_table = "log_openshift_release_advisory"

    log_openshift_release_advisory_id = models.AutoField(primary_key=True)
    openshift_version = models.CharField(max_length=50, null=False, blank=False)
    brew_event = models.CharField(max_length=100, null=False, blank=False)
    objects = OpenShiftCurrentAdvisoryManager()
