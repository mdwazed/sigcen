# Generated by Django 2.2.7 on 2019-12-26 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_slip', '0024_auto_20191221_0511'),
    ]

    operations = [
        migrations.AddField(
            model_name='letter',
            name='addr_line_1',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user_type',
            field=models.CharField(blank=True, choices=[('uc', 'Unit clk'), ('sc', 'Sigcen clk'), ('ad', 'Admin')], default='uc', max_length=2, null=True),
        ),
    ]
