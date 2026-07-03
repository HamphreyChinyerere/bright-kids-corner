# Generated manually for CodingGame model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_timetableslot'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodingGame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('game_type', models.CharField(
                    choices=[('scratch', 'Scratch (MIT Block)'), ('woofjs', 'WoofJS (JavaScript Canvas)')],
                    max_length=20,
                )),
                ('description', models.TextField(blank=True)),
                ('source_identifier', models.CharField(
                    help_text='Paste Scratch Project ID OR WoofJS project URL token here',
                    max_length=255,
                )),
                ('module', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='coding_games',
                    to='core.coursemodule',
                )),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
