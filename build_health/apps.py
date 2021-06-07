# from django.apps import AppConfig
# import sys
#
#
# class BuildHealthConfig(AppConfig):
#     name = 'build_health'
#     verbose_name = "Build Health Application"
#
#     def ready(self):
#         from lib.cron_schedules import start_scheduler_thread
#         if sys.argv[1] == 'runserver':
#             start_scheduler_thread()
