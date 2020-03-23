# Generated by Django 2.2.7 on 2020-03-20 13:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transit_slip', '0037_auto_20200229_2249'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='unit_code',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='letter',
            name='transit_slip',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ltrs', to='transit_slip.TransitSlip'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user_type',
            field=models.CharField(blank=True, choices=[('uc', 'Unit clk'), ('sc', 'Sigcen clk'), ('ad', 'Admin')], default='uc', max_length=2, null=True),
        ),
    ]
