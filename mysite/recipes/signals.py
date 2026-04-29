from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Comment, Post, RecipeIngredient


PUBLISHED_POST_IDS_CACHE_KEY = "recipes.published_post_ids"


def _refresh_recipe_counts(post_id):
    ingredient_count = RecipeIngredient.objects.filter(post_id=post_id).count()
    comment_count = Comment.objects.filter(post_id=post_id, active=True).count()

    Post.objects.filter(pk=post_id).update(
        ingredient_count=ingredient_count,
        comment_count=comment_count,
    )


def _clear_recipe_caches():
    """Clear all recipe-related caches to ensure consistency."""
    cache.delete(PUBLISHED_POST_IDS_CACHE_KEY)
    # Clear all search cache keys by using a pattern (if using a cache backend that supports it)
    # For now, just delete known cache keys on updates
    try:
        cache.delete_pattern("recipes.post_list_count.*")
        cache.delete_pattern("recipes.search.*")
    except (AttributeError, NotImplementedError):
        # If the backend doesn't support delete_pattern, that's okay
        # The caches will just expire naturally
        pass


@receiver([post_save, post_delete], sender=RecipeIngredient)
def sync_recipe_ingredient_counts(sender, instance, **kwargs):
    _refresh_recipe_counts(instance.post_id)
    _clear_recipe_caches()


@receiver([post_save, post_delete], sender=Comment)
def sync_comment_counts(sender, instance, **kwargs):
    _refresh_recipe_counts(instance.post_id)
    _clear_recipe_caches()


@receiver([post_save, post_delete], sender=Post)
def clear_published_post_cache(sender, **kwargs):
    _clear_recipe_caches()
