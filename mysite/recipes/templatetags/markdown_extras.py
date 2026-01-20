from django import template
from django.utils.safestring import mark_safe

try:
    from markdown import markdown as md_convert
except Exception:
    md_convert = None

register = template.Library()

@register.filter(name="md")
def markdown_filter(value):
    if value is None:
        return ""
    if md_convert is None:
        # Fallback: return plain text if markdown isn't available
        return value
    html = md_convert(
        str(value),
        extensions=[
            "fenced_code",
            "tables",
            "sane_lists",
            "smarty",
        ],
        output_format="html5",
    )
    return mark_safe(html)
