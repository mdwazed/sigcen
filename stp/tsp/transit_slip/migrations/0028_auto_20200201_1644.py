# Generated by Django 2.2.7 on 2020-02-01 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_slip', '0027_auto_20200201_0942'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='letter',
            name='received_at_sigcen',
        ),
        migrations.RemoveField(
            model_name='letter',
            name='received_by_sigcen',
        ),
        migrations.RemoveField(
            model_name='letterreceipt',
            name='from_unit',
        ),
        migrations.RemoveField(
            model_name='letterreceipt',
            name='received_dt',
        ),
        migrations.AddField(
            model_name='letterreceipt',
            name='received_at_sigcen',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user_type',
            field=models.CharField(blank=True, choices=[('uc', 'Unit clk'), ('ad', 'Admin'), ('sc', 'Sigcen clk')], default='uc', max_length=2, null=True),
        ),
    ]