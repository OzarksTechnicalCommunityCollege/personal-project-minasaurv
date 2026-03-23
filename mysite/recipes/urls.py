from django.urls import path
from . import views

app_name = "recipes"
urlpatterns = [
    # Post list page
    path("", views.post_list, name="post_list"),
    # Post list filtered by tag
    path("tag/<slug:tag_slug>/", views.post_list, name="post_list_by_tag"),
    # Post detail page
    path(
        "<int:year>/<int:month>/<int:day>/<slug:post>/",
        views.post_detail,
        name="post_detail",
    ),
    # Comment submission endpoint
    path("<int:post_id>/comment/", views.post_comment, name="post_comment"),
    # Search page
    path("search/", views.post_search, name="post_search"),
]
