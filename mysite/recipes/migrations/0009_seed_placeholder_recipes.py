from datetime import timedelta

from django.conf import settings
from django.db import migrations
from django.utils import timezone


def _get_or_create_placeholder_user(apps):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)

    user, created = User.objects.get_or_create(
        username="placeholderchef",
        defaults={
            "email": "placeholderchef@example.com",
        },
    )

    if created and hasattr(user, "set_unusable_password"):
        user.set_unusable_password()
        user.save()

    return user


def seed_placeholder_recipes(apps, schema_editor):
    Post = apps.get_model("recipes", "Post")
    Ingredient = apps.get_model("recipes", "Ingredient")
    RecipeIngredient = apps.get_model("recipes", "RecipeIngredient")
    RecipeStep = apps.get_model("recipes", "RecipeStep")

    author = _get_or_create_placeholder_user(apps)
    now = timezone.now()

    placeholder_data = [
        {
            "title": "Capybara Cozy Tomato Pasta",
            "slug": "capybara-cozy-tomato-pasta",
            "content": "A cozy tomato pasta with garlic, basil, and parmesan for an easy weeknight dinner.",
            "servings": 4,
            "time": 30,
            "ingredients": [
                ("spaghetti", "400", "g", ""),
                ("olive oil", "2", "tbsp", ""),
                ("garlic", "4", "cloves", "minced"),
                ("crushed tomatoes", "1", "can", "about 800g"),
                ("fresh basil", "1", "handful", "roughly chopped"),
                ("parmesan", "50", "g", "grated"),
            ],
            "steps": [
                "Cook spaghetti in salted boiling water until al dente.",
                "Saute garlic in olive oil over medium heat until fragrant.",
                "Stir in tomatoes and simmer for 12 minutes.",
                "Fold in basil, then toss with drained pasta.",
                "Serve hot with grated parmesan.",
            ],
        },
        {
            "title": "Sunny Sheet Pan Lemon Chicken",
            "slug": "sunny-sheet-pan-lemon-chicken",
            "content": "Tender lemon chicken with roasted vegetables, all done on one sheet pan.",
            "servings": 4,
            "time": 45,
            "ingredients": [
                ("chicken thighs", "8", "pieces", "bone-in"),
                ("baby potatoes", "500", "g", "halved"),
                ("carrots", "3", "", "cut into sticks"),
                ("lemon", "1", "", "zest and juice"),
                ("olive oil", "3", "tbsp", ""),
                ("dried oregano", "1", "tsp", ""),
            ],
            "steps": [
                "Preheat oven to 220C and line a sheet pan.",
                "Toss potatoes and carrots with olive oil and oregano.",
                "Arrange vegetables and chicken on the pan.",
                "Season with lemon zest, lemon juice, salt, and pepper.",
                "Roast for 35 minutes until chicken is cooked through.",
            ],
        },
        {
            "title": "Midnight Chocolate Mug Cake",
            "slug": "midnight-chocolate-mug-cake",
            "content": "A quick single-serve chocolate cake made in the microwave for late-night cravings.",
            "servings": 1,
            "time": 5,
            "ingredients": [
                ("all-purpose flour", "4", "tbsp", ""),
                ("cocoa powder", "2", "tbsp", ""),
                ("sugar", "2", "tbsp", ""),
                ("milk", "3", "tbsp", ""),
                ("vegetable oil", "2", "tbsp", ""),
                ("chocolate chips", "1", "tbsp", "optional"),
            ],
            "steps": [
                "Whisk flour, cocoa powder, and sugar in a microwave-safe mug.",
                "Stir in milk and oil until smooth.",
                "Fold in chocolate chips if using.",
                "Microwave on high for 70 to 90 seconds.",
                "Let cool for 1 minute, then enjoy.",
            ],
        },
        {
            "title": "Garden Crunch Rainbow Salad",
            "slug": "garden-crunch-rainbow-salad",
            "content": "A colorful salad with crunchy vegetables and a tangy honey-mustard dressing.",
            "servings": 3,
            "time": 20,
            "ingredients": [
                ("romaine lettuce", "1", "head", "chopped"),
                ("cucumber", "1", "", "sliced"),
                ("red bell pepper", "1", "", "thinly sliced"),
                ("carrot", "1", "", "shredded"),
                ("sweet corn", "1", "cup", "cooked"),
                ("honey mustard dressing", "4", "tbsp", ""),
            ],
            "steps": [
                "Wash and prepare all vegetables.",
                "Combine lettuce, cucumber, pepper, carrot, and corn in a bowl.",
                "Add dressing and toss gently.",
                "Taste and adjust seasoning.",
                "Serve immediately while crunchy.",
            ],
        },
    ]

    for offset, recipe in enumerate(placeholder_data):
        post, created = Post.objects.get_or_create(
            slug=recipe["slug"],
            defaults={
                "title": recipe["title"],
                "author": author,
                "content": recipe["content"],
                "publish": now - timedelta(days=offset),
                "status": "PB",
                "servings": recipe["servings"],
                "time": recipe["time"],
            },
        )

        if not created:
            continue

        for index, (name, quantity, unit, notes) in enumerate(recipe["ingredients"]):
            ingredient, _ = Ingredient.objects.get_or_create(name=name)
            RecipeIngredient.objects.create(
                post=post,
                ingredient=ingredient,
                quantity=quantity,
                unit=unit,
                notes=notes,
                display_order=index,
            )

        for step_number, instruction in enumerate(recipe["steps"], start=1):
            RecipeStep.objects.create(
                post=post,
                step_number=step_number,
                instruction=instruction,
            )


def remove_placeholder_recipes(apps, schema_editor):
    Post = apps.get_model("recipes", "Post")
    slugs = [
        "capybara-cozy-tomato-pasta",
        "sunny-sheet-pan-lemon-chicken",
        "midnight-chocolate-mug-cake",
        "garden-crunch-rainbow-salad",
    ]
    Post.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0008_remove_post_instructions_remove_post_substitution"),
    ]

    operations = [
        migrations.RunPython(seed_placeholder_recipes, remove_placeholder_recipes),
    ]
