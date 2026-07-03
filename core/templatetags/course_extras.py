from django import template

from core.course_images import get_course_thumbnail_url

register = template.Library()


@register.simple_tag
def catalog_thumbnail(course_name):
    """Thumbnail URL for static catalog cards (by course title)."""
    return get_course_thumbnail_url(title=course_name)


@register.filter
def course_thumbnail_url(course):
    """Thumbnail URL for a Course model instance."""
    if course.thumbnail:
        return course.thumbnail.url
    return get_course_thumbnail_url(
        subject=course.subject,
        title=course.title,
        slug=course.slug,
    )
