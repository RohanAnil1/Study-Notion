from markupsafe import Markup

def nl2br(value):
    """Convert newlines to <br> tags."""
    if not value:
        return ""
    return Markup(value.replace('\n', '<br>\n'))

def init_app(app):
    """Register custom filters with the Flask app."""
    app.jinja_env.filters['nl2br'] = nl2br 