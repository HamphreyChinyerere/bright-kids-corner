# Generated manually for course outline & enrollment features

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_embeddedgame_kidsdailychallenge_vrcontent_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('order', models.PositiveIntegerField(default=1)),
                ('description', models.TextField(blank=True, default='')),
                ('lesson_summary', models.CharField(blank=True, default='', help_text='Short label for lessons in this topic (e.g. "4 lessons")', max_length=255)),
                ('exercise_title', models.CharField(blank=True, default='', max_length=255)),
                ('exercise_description', models.TextField(blank=True, default='')),
                ('project_title', models.CharField(blank=True, default='', max_length=255)),
                ('project_description', models.TextField(blank=True, default='')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modules', to='core.course')),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('course', 'order')},
            },
        ),
        migrations.CreateModel(
            name='CourseExam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('duration_minutes', models.PositiveIntegerField(default=60)),
                ('course', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='final_exam', to='core.course')),
            ],
        ),
        migrations.AddField(
            model_name='assignmenttask',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assignment_tasks', to='core.course'),
        ),
        migrations.AddField(
            model_name='assignmenttask',
            name='is_final_exam',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='assignmenttask',
            name='module',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exercises', to='core.coursemodule'),
        ),
        migrations.AddField(
            model_name='projectsandbox',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_projects', to='core.course'),
        ),
        migrations.AddField(
            model_name='projectsandbox',
            name='module',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='core.coursemodule'),
        ),
        migrations.AlterField(
            model_name='projectsandbox',
            name='project_type',
            field=models.CharField(choices=[('Scratch', 'Scratch'), ('WoofJS', 'WoofJS'), ('VanillaJS', 'VanillaJS'), ('Python', 'Python')], max_length=50),
        ),
    ]
