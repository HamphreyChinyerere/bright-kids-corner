"""
Default course thumbnail URLs (Unsplash) when no uploaded file is set.
"""

# Subject/title → 800×500 crop-friendly Unsplash images
COURSE_THUMBNAIL_URLS = {
    'Python': 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&h=500&fit=crop&q=80',
    'Python Coding': 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&h=500&fit=crop&q=80',
    'JavaScript': 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=800&h=500&fit=crop&q=80',
    'HTML & CSS': 'https://images.unsplash.com/photo-1547658719-da2b51169191?w=800&h=500&fit=crop&q=80',
    'IT Basics': 'https://images.unsplash.com/photo-1517694712202-14dd953815a9?w=800&h=500&fit=crop&q=80',
    'Chemistry': 'https://images.unsplash.com/photo-1532094349886-49202e6d44b8?w=800&h=500&fit=crop&q=80',
    'Physics': 'https://images.unsplash.com/photo-1636466497215-26d93ee9b0ec?w=800&h=500&fit=crop&q=80',
    'Mathematics': 'https://images.unsplash.com/photo-1635070041078-ebdb9d88b782?w=800&h=500&fit=crop&q=80',
    'Geography': 'https://images.unsplash.com/photo-1526778548025-fa2cf3cd3ef8?w=800&h=500&fit=crop&q=80',
    'Astronomy': 'https://images.unsplash.com/photo-1419242902214-272b403b9366?w=800&h=500&fit=crop&q=80',
    'Engineering': 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&h=500&fit=crop&q=80',
}


def get_course_thumbnail_url(*, subject='', title='', slug=''):
    """Resolve a display URL for a course thumbnail."""
    for key in (title, subject):
        if key and key in COURSE_THUMBNAIL_URLS:
            return COURSE_THUMBNAIL_URLS[key]
    seed = (slug or title or subject or 'course').replace(' ', '-').lower()
    return f'https://picsum.photos/seed/{seed}/800/500'
