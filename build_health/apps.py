from django.apps import AppConfig


class BuildHealthConfig(AppConfig):
    name = 'build_health'
    verbose_name = "Build Health Application"

    def ready(self):
        from lib.cron_schedules import start_scheduler_thread
        start_scheduler_thread()
