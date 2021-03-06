# Generated by Django 2.0.1 on 2018-01-18 02:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0006_auto_20180115_2248'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='AttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=100)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign.Attribute')),
                ('thing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign.Thing')),
            ],
        ),
        migrations.CreateModel(
            name='ThingType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='attribute',
            name='thing_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign.ThingType'),
        ),
        migrations.AddField(
            model_name='thing',
            name='thing_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='campaign.ThingType'),
        ),
    ]
