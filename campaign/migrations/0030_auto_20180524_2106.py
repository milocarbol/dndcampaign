# Generated by Django 2.0.4 on 2018-05-25 04:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0029_randomizerattributecategory_can_combine_with_self'),
    ]

    operations = [
        migrations.CreateModel(
            name='RandomizerAttributeCategorySynonym',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='randomizerattributecategory',
            name='name_synonym_first',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='randomizerattributecategory',
            name='name_synonym_last',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='randomizerattributecategorysynonym',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign.RandomizerAttributeCategory'),
        ),
        migrations.AlterUniqueTogether(
            name='randomizerattributecategorysynonym',
            unique_together={('name', 'category')},
        ),
    ]