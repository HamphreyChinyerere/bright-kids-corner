import os
os.environ['DJANGO_SETTINGS_MODULE']='bright_project.settings'
from django.conf import settings
print(settings.STATIC_URL)
