# Generated by Django 4.2.16 on 2024-10-14 15:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("member", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Schedule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("leetcode_username", models.CharField(max_length=256)),
                ("created_date", models.DateTimeField(auto_now=True)),
                ("last_update", models.DateTimeField(auto_now_add=True)),
                ("expire_date", models.DateTimeField(auto_now=True)),
                (
                    "server",
                    models.CharField(
                        choices=[("CN", "China Mainland"), ("US", "United States")],
                        default="US",
                        max_length=2,
                    ),
                ),
                (
                    "member_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="member.member"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Problem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("problem_name", models.CharField(max_length=256)),
                ("status", models.BooleanField(default=False)),
                ("done_date", models.DateTimeField(auto_now=True)),
                (
                    "schedule_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="check.schedule"
                    ),
                ),
            ],
        ),
    ]
