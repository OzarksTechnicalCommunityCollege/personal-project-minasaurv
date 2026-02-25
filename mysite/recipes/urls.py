from django.urls import path
from . import views

app_name = 'recipes'
urlpatterns = [
    # Post list page
    path('', views.post_list, name='post_list'),
    # Post detail page
    path(
        '<int:year>/<int:month>/<int:day>/<slug:post>/',
        views.post_detail,
        name='post_detail'
    ),
    # Comment submission endpoint
    path('<int:post_id>/comment/', views.post_comment, name='post_comment'),
]