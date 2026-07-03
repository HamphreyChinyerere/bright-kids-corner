import os
import django

# Use actual project settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bright_project.settings')
django.setup()

from core.models import EmbeddedGame

# Normalize age groups to the choices defined in models
AGE_MAP = {
    'All Ages': 'all',
    'all': 'all',
    '5-8': '5-8',
    '8-12': '8-12',
    '12-16': '12-16',
    '13+': '12-16',
    '16+': '12-16',
}

python_games = [
    {
        "title": "Blockly Python Sequencer",
        "description": "Arrange structural logic blocks to auto-generate and study clean Python procedural scripts in real-time.",
        "category": "coding",
        "age_group": "All Ages",
        "embed_url": "https://blockly-demo.appspot.com/blockly/demos/code/index.html?lang=en",
        "is_featured": True
    },
    {
        "title": "Python Bug-Hunting Theatre",
        "description": "Locate and resolve syntax issues, indentation breaks, and structural logic bugs within active scripts.",
        "category": "coding",
        "age_group": "13+",
        "embed_url": "https://trinket.io/embed/python3/bf88bdfcc5?toggleCode=true",
        "is_featured": False
    },
    {
        "title": "Interactive Terminal State Engine",
        "description": "Manipulate state validation structures, conditional data loops, and inputs directly inside a live Python3 terminal view.",
        "category": "coding",
        "age_group": "16+",
        "embed_url": "https://trinket.io/embed/python3/3d8d7cd2b7?toggleCode=true",
        "is_featured": False
    }
]

for game_data in python_games:
    # Ensure age_group matches model choices (fallback to 'all')
    raw_age = game_data.get('age_group', '').strip()
    mapped_age = AGE_MAP.get(raw_age, AGE_MAP.get(raw_age.lower(), 'all'))
    create_data = {
        'description': game_data['description'],
        'category': game_data['category'],
        'age_group': mapped_age,
        'embed_url': game_data['embed_url'],
        'is_featured': game_data['is_featured'],
    }

    game, created = EmbeddedGame.objects.get_or_create(
        title=game_data['title'],
        defaults=create_data
    )

    if created:
        print(f"Successfully added game: {game.title}")
    else:
        print(f"Game already exists: {game.title}")
