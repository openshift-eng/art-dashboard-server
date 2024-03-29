# Generated by Django 3.0.7 on 2020-07-27 19:23

import build.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AutoCompleteRecord',
            fields=[
                ('updated_at', build.models.UnixTimestampField(auto_created=True, null=True)),
                ('created_at', build.models.UnixTimestampField(auto_created=True, null=True)),
                ('log_autocomplete_record_id', models.AutoField(primary_key=True, serialize=False)),
                ('type', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=300)),
            ],
            options={
                'db_table': 'log_autocomplete_record',
            },
        ),
    ]
