# Generated by Django 4.2.16 on 2025-02-28 01:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("check", "0008_schedule_sheet_row"),
    ]

    operations = [
        migrations.AlterField(
            model_name="problem",
            name="problem_code",
            field=models.IntegerField(default=-1, null=True),
        ),
        migrations.AlterField(
            model_name="problem",
            name="problem_slug",
            field=models.CharField(max_length=256, unique=True),
        ),
    ]
