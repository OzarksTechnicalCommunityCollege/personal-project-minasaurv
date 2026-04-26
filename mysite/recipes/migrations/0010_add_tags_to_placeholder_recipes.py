from django.db import migrations
from django.utils.text import slugify


PLACEHOLDER_TAGS = {
    "capybara-cozy-tomato-pasta": ["pasta", "vegetarian", "comfort food"],
    "sunny-sheet-pan-lemon-chicken": ["chicken", "sheet pan", "weeknight"],
    "midnight-chocolate-mug-cake": ["dessert", "quick", "chocolate"],
    "garden-crunch-rainbow-salad": ["salad", "fresh", "healthy"],
}


def add_placeholder_tags(apps, schema_editor):
    Post = apps.get_model("recipes", "Post")
    Tag = apps.get_model("taggit", "Tag")
    TaggedItem = apps.get_model("taggit", "TaggedItem")
    ContentType = apps.get_model("contenttypes", "ContentType")

    post_content_type = ContentType.objects.get_for_model(Post)

    for slug, tag_names in PLACEHOLDER_TAGS.items():
        post = Post.objects.get(slug=slug)

        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(
                name=tag_name,
                defaults={"slug": slugify(tag_name)},
            )
            TaggedItem.objects.get_or_create(
                content_type=post_content_type,
                object_id=post.pk,
                tag=tag,
            )


def remove_placeholder_tags(apps, schema_editor):
    Post = apps.get_model("recipes", "Post")
    TaggedItem = apps.get_model("taggit", "TaggedItem")
    ContentType = apps.get_model("contenttypes", "ContentType")

    post_content_type = ContentType.objects.get_for_model(Post)
    slugs = list(PLACEHOLDER_TAGS.keys())
    post_ids = list(Post.objects.filter(slug__in=slugs).values_list("pk", flat=True))

    TaggedItem.objects.filter(
        content_type=post_content_type,
        object_id__in=post_ids,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0009_seed_placeholder_recipes"),
        ("taggit", "0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(add_placeholder_tags, remove_placeholder_tags),
    ]
