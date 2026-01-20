from django.shortcuts import get_object_or_404, render
from django.http import Http404
from .models import Post

# Post list view
def post_list(request):
    posts = Post.published.all()
    return render(request, 'recipes/post/list.html', {'posts': posts})

# Post detail view
def post_detail(request, id):
    post = get_object_or_404(Post, id=id, status=Post.Status.PUBLISHED)
    return render(request, 'recipes/post/detail.html', {'post': post})