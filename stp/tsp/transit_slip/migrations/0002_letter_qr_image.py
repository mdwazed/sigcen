# Generated by Django 2.2.7 on 2019-11-16 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_slip', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='letter',
            name='qr_image',
            field=models.ImageField(blank=True, upload_to='qr_code_image/'),
        ),
    ]
