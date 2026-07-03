# Generated for weekly timetable feature

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_coursemodule_courseexam_course_links'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TimetableSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')])),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('title', models.CharField(max_length=255)),
                ('slot_type', models.CharField(choices=[('course', 'Course'), ('study', 'Study'), ('exam', 'Exam'), ('break', 'Break'), ('custom', 'Custom')], default='custom', max_length=20)),
                ('notes', models.TextField(blank=True, default='')),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='timetable_slots', to='core.course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timetable_slots', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['weekday', 'start_time'],
            },
        ),
    ]
