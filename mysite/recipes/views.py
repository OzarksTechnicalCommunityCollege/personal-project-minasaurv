from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Post
from .forms import CommentForm

# Post list view
def post_list(request):
    post_qs = Post.published.all()
    paginator = Paginator(post_qs, 5)  # 5 posts per page
    page = request.GET.get('page', 1)
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage: 
        posts = paginator.page(paginator.num_pages)

    return render(request, 'recipes/post/list.html', {
        'posts': posts,
    })

# Post detail view
def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        slug=post,
        status=Post.Status.PUBLISHED,
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )
    # Display only active comments in chronological order
    comments = post.comments.filter(active=True)
    form = CommentForm()
    return render(
        request,
        'recipes/post/detail.html',
        {
            'post': post,
            'comments': comments,
            'form': form,
        },
    )


# Post comment submission view
def post_comment(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED,
    )
    comment = None

    # Handle comment form submission
    if request.method == 'POST':
        form = CommentForm(data=request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
    else:
        form = CommentForm()

    return render(
        request,
        'recipes/post/comment.html',
        {
            'post': post,
            'form': form,
            'comment': comment,
        },
    )