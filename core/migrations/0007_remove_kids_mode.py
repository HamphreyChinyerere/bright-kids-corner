# Generated manually — remove Kids Mode models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_codinggame'),
    ]

    operations = [
        migrations.DeleteModel(
            name='KidsAchievement',
        ),
        migrations.DeleteModel(
            name='KidsDailyChallenge',
        ),
        migrations.DeleteModel(
            name='KidsProfile',
        ),
    ]
