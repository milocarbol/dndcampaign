# Generated by Django 2.0.1 on 2018-03-03 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0014_auto_20180302_0632'),
    ]

    operations = [
        migrations.AddField(
            model_name='attribute',
            name='is_thing',
            field=models.BooleanField(default=False),
        ),
    ]
