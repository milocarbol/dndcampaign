# Generated by Django 2.0.4 on 2018-06-01 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0053_auto_20180531_1949'),
    ]

    operations = [
        migrations.AddField(
            model_name='randomizerattribute',
            name='max_options_to_use',
            field=models.IntegerField(default=1),
        ),
    ]