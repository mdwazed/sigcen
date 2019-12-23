# Generated by Django 2.2.7 on 2019-12-20 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_slip', '0022_profile_user_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='transitslip',
            name='despatched_on',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user_type',
            field=models.CharField(blank=True, choices=[('ad', 'Admin'), ('uc', 'Unit clk'), ('sc', 'Sigcen clk')], default='uc', max_length=2, null=True),
        ),
    ]
