# Generated by Django 2.2.7 on 2019-11-30 18:20

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('transit_slip', '0013_auto_20191129_0911'),
    ]

    operations = [
        migrations.AddField(
            model_name='letter',
            name='receive_by_sigcen',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='letter',
            name='received_at_sigcen',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
