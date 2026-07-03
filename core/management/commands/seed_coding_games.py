from django.core.management.base import BaseCommand

from core.models import CodingGame, Course, CourseModule


class Command(BaseCommand):
    help = 'Seed Scratch and WoofJS CodingGame sandboxes linked to course modules.'

    def handle(self, *args, **options):
        course = Course.objects.filter(slug='python-coding').first()
        modules = list(course.modules.order_by('order')[:2]) if course else []

        samples = [
            {
                'title': 'Sprite Motion Lab',
                'game_type': 'scratch',
                'description': (
                    'Use block-based events to move a sprite across the stage and '
                    'respond to keyboard input.'
                ),
                'source_identifier': '60917032',
                'module': modules[0] if len(modules) > 0 else None,
            },
            {
                'title': 'Canvas Animation Studio',
                'game_type': 'woofjs',
                'description': (
                    'Write JavaScript on the WoofJS canvas to animate shapes and '
                    'build interactive loops.'
                ),
                'source_identifier': 'https://woofjs.com/full',
                'module': modules[1] if len(modules) > 1 else None,
            },
        ]

        for data in samples:
            module = data.pop('module')
            defaults = {**data}
            if module:
                obj, created = CodingGame.objects.update_or_create(
                    module=module,
                    game_type=defaults['game_type'],
                    defaults=defaults,
                )
            else:
                obj, created = CodingGame.objects.update_or_create(
                    title=defaults['title'],
                    game_type=defaults['game_type'],
                    module=None,
                    defaults=defaults,
                )
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'{verb}: {obj}')

        self.stdout.write(self.style.SUCCESS('Coding games seeded.'))
