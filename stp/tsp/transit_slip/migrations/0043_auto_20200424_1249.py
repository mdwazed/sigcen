# Generated by Django 2.2.7 on 2020-04-24 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_slip', '0042_auto_20200407_0758'),
    ]

    operations = [
        migrations.AddField(
            model_name='letter',
            name='through_sigcen',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='letter',
            name='classification',
            field=models.CharField(blank=True, choices=[('sc', 'Secret'), ('ts', 'Top Secret'), ('rs', 'Restricted'), ('cf', 'Confidential'), ('uc', 'Unclass')], default='rs', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user_type',
            field=models.CharField(blank=True, choices=[('uc', 'Unit clk'), ('ad', 'Admin'), ('sc', 'Sigcen clk')], default='uc', max_length=2, null=True),
        ),
    ]
