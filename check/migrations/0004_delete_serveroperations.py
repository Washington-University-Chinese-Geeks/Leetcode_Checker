# Generated by Django 4.2.10 on 2024-10-29 01:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("check", "0003_rename_server_schedule_server_region_and_more"),
    ]

    operations = [
        migrations.DeleteModel(name="ServerOperations",),
    ]
