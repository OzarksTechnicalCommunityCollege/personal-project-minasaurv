from django.apps import AppConfig


class RecipesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
    
    def ready(self):
        # Ensure custom templatetags are importable in all environments
        try:
            import recipes.templatetags.markdown_extras  # noqa: F401
        except Exception:
            # If import fails (e.g., during certain management commands), skip
            pass
