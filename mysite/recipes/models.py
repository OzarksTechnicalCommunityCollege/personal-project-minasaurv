from django.db import models
from django.utils import timezone
from django.conf import settings

# Custom manager to retrieve published posts
class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)

# Recipe post model
class Post(models.Model):

    # Metadata
    class Meta:
        ordering = ['-publish']
        indexes = [models.Index(fields=['-publish'])]

    # Publish status
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    # Model fields
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipe_posts'
    )
    content = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT
    )
    objects = models.Manager()
    published = PublishedManager()

    def __str__(self):
        return self.title