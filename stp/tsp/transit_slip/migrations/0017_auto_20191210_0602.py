# Generated by Django 2.2.7 on 2019-12-10 06:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transit_slip', '0016_auto_20191201_1704'),
    ]

    operations = [
        migrations.RenameField(
            model_name='letter',
            old_name='receive_by_sigcen',
            new_name='received_by_sigcen',
        ),
    ]
