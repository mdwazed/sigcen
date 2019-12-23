# Generated by Django 2.2.7 on 2019-12-17 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_slip', '0021_auto_20191215_0513'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='user_type',
            field=models.CharField(blank=True, choices=[('uc', 'Unit clk'), ('sc', 'Sigcen clk'), ('ad', 'Admin')], default='uc', max_length=2, null=True),
        ),
    ]
