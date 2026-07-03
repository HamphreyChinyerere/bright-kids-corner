def streamlined_state(request):
    """Global context processor to inject streamlined view state into templates."""
    return {
        'is_streamlined_view': request.session.get('is_streamlined_view', False)
    }
