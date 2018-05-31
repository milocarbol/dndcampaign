# Generated by Django 2.0.4 on 2018-05-31 22:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0050_randomizerattributeoption_weight'),
    ]

    operations = [
        migrations.CreateModel(
            name='Weight',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_to_weight', models.CharField(max_length=50)),
                ('weight', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='WeightPreset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign.Campaign')),
            ],
        ),
        migrations.RemoveField(
            model_name='randomizerattributeoption',
            name='weight',
        ),
        migrations.AddField(
            model_name='weight',
            name='weight_preset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign.WeightPreset'),
        ),
        migrations.AlterUniqueTogether(
            name='weightpreset',
            unique_together={('name', 'campaign')},
        ),
        migrations.AlterUniqueTogether(
            name='weight',
            unique_together={('name_to_weight', 'weight_preset')},
        ),
    ]
