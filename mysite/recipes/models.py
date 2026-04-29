from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from taggit.managers import TaggableManager


# Custom manager to retrieve published posts
class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


# Recipe post model
class Post(models.Model):

    # Metadata
    class Meta:
        ordering = ["-publish"]
        indexes = [models.Index(fields=["-publish"])]

    # Publish status
    class Status(models.TextChoices):
        DRAFT = "DF", "Draft"
        PUBLISHED = "PB", "Published"

    # Model fields
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date="publish")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipe_posts"
    )
    content = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2, choices=Status.choices, default=Status.DRAFT
    )
    # Additional recipe metadata
    servings = models.PositiveIntegerField(
        null=True, blank=True, help_text="Number of servings"
    )
    time = models.PositiveIntegerField(
        null=True, blank=True, help_text="Preparation/cook time in minutes"
    )
    tags = TaggableManager(blank=True)
    ingredients = models.ManyToManyField(
        "Ingredient",
        through="RecipeIngredient",
        related_name="posts",
        blank=True,
    )
    ingredient_count = models.PositiveIntegerField(default=0, editable=False)
    comment_count = models.PositiveIntegerField(default=0, editable=False)
    objects = models.Manager()
    published = PublishedManager()

    def __str__(self):
        return self.title

    # Get absolute URL for post
    def get_absolute_url(self):
        return reverse(
            "recipes:post_detail",
            args=[self.publish.year, self.publish.month, self.publish.day, self.slug],
        )


# Comment model for recipe posts
class Comment(models.Model):

    # Relationship and author info
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    # Metadata
    class Meta:
        ordering = ["created"]
        indexes = [
            models.Index(fields=["created"]),
            models.Index(fields=["active"]),
        ]

    # String representation
    def __str__(self):
        return f"Comment by {self.name} on {self.post}"


# Ingredient catalog model
class Ingredient(models.Model):
    name = models.CharField(max_length=120, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# Junction model linking recipes and ingredients
class RecipeIngredient(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, related_name="used_in_recipes"
    )
    quantity = models.CharField(max_length=50, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["post", "ingredient", "display_order"],
                name="unique_recipe_ingredient_order",
            )
        ]

    def __str__(self):
        qty_part = f"{self.quantity} " if self.quantity else ""
        unit_part = f"{self.unit} " if self.unit else ""
        return f"{self.post}: {qty_part}{unit_part}{self.ingredient}".strip()


# Ordered recipe instruction steps
class RecipeStep(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="recipe_steps"
    )
    step_number = models.PositiveIntegerField()
    instruction = models.TextField()

    class Meta:
        ordering = ["step_number", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["post", "step_number"], name="unique_recipe_step_number"
            )
        ]

    def __str__(self):
        return f"{self.post} - Step {self.step_number}"
