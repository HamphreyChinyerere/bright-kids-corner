import os
import django

# Use project settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bright_project.settings')
django.setup()

from core.models import EmbeddedGame

# Map provided age labels to model choices
AGE_MAP = {
    'All Ages': 'all',
    'all': 'all',
    '12+': '12-16',
    '12-16': '12-16',
}

entries = [
    {
        'title': 'Visual Block Coding Sandbox (ScratchJr Style)',
        'description': 'An interactive visual sandbox using block architecture to build sequences, animations, and stories without typing code.',
        'category': 'coding',
        'age_group': 'All Ages',
        'embed_url': 'https://turbowarp.org/embed.html?project_id=101213312&addons=clones',
        'is_featured': True,
    },
    {
        'title': 'WoofJS Real-Time Coding Canvas',
        'description': 'Transition from blocks to real JavaScript. Write clean text commands to create interactive games and animations instantly.',
        'category': 'coding',
        'age_group': '12+',
        'embed_url': 'https://woofjs.com/create.html',
        'is_featured': True,
    }
]

for data in entries:
    age_raw = data.get('age_group', '').strip()
    age = AGE_MAP.get(age_raw, 'all')

    defaults = {
        'description': data['description'],
        'category': data['category'],
        'age_group': age,
        'embed_url': data['embed_url'],
        'is_featured': data['is_featured'],
    }

    game, created = EmbeddedGame.objects.get_or_create(title=data['title'], defaults=defaults)
    if created:
        print(f"Created: {game.title}")
    else:
        # Optionally update fields if you want to keep them in sync uncomment below
        # for k, v in defaults.items():
        #     setattr(game, k, v)
        # game.save()
        print(f"Already exists: {game.title}")
