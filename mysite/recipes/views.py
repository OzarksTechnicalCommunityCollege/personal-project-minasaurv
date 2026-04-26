import random

from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth.decorators import login_required

try:
    from django.contrib.postgres.search import (
        SearchVector,
        SearchQuery,
        SearchRank,
        TrigramSimilarity,
    )

    POSTGRES_SEARCH_AVAILABLE = True
except ImportError:
    POSTGRES_SEARCH_AVAILABLE = False
from taggit.models import Tag
from .models import Post
from .forms import CommentForm, SearchForm


def _commenter_name(user):
    full_name = user.get_full_name().strip()
    if full_name:
        return full_name

    social_account = user.social_auth.filter(provider="google-oauth2").first()
    if social_account:
        extra_data = social_account.extra_data or {}
        google_name = (extra_data.get("name") or "").strip()
        if google_name:
            return google_name
        given_name = (extra_data.get("given_name") or "").strip()
        family_name = (extra_data.get("family_name") or "").strip()
        combined = f"{given_name} {family_name}".strip()
        if combined:
            return combined

    return user.username or "Authenticated User"


def _commenter_email(user):
    if user.email:
        return user.email

    social_account = user.social_auth.filter(provider="google-oauth2").first()
    if social_account:
        social_email = (social_account.extra_data or {}).get("email")
        if social_email:
            return social_email

    return "no-reply@example.com"


# Post list view
def post_list(request, tag_slug=None):
    post_qs = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_qs = post_qs.filter(tags__in=[tag])

    paginator = Paginator(post_qs, 5)  # 5 posts per page
    page = request.GET.get("page", 1)
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(
        request,
        "recipes/post/list.html",
        {
            "posts": posts,
            "tag": tag,
        },
    )


# Post detail view
def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post.objects.prefetch_related("recipe_ingredients__ingredient", "recipe_steps"),
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
        "recipes/post/detail.html",
        {
            "post": post,
            "comments": comments,
            "form": form,
        },
    )


# Post comment submission view
@login_required
def post_comment(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED,
    )
    comment = None

    # Handle comment form submission
    if request.method == "POST":
        form = CommentForm(data=request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.name = _commenter_name(request.user)
            comment.email = _commenter_email(request.user)
            comment.save()
    else:
        form = CommentForm()

    return render(
        request,
        "recipes/post/comment.html",
        {
            "post": post,
            "form": form,
            "comment": comment,
        },
    )


# Recipe search view
def post_search(request):
    form = SearchForm()
    query = None
    results = []
    search_method = "Basic Search"

    if "query" in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"].strip()[:250]

            if not query:
                return render(
                    request,
                    "recipes/post/search.html",
                    {
                        "form": form,
                        "query": query,
                        "results": results,
                        "search_method": search_method,
                    },
                )

            # Use basic database search with Q objects
            # Build comprehensive Q objects for search
            search_terms = query.split()
            q_objects = Q()

            for term in search_terms:
                q_objects |= (
                    Q(title__icontains=term)
                    | Q(content__icontains=term)
                    | Q(recipe_ingredients__ingredient__name__icontains=term)
                    | Q(recipe_steps__instruction__icontains=term)
                    | Q(tags__name__icontains=term)
                )

            results = (
                Post.published.filter(q_objects)
                .distinct()
                .order_by("-publish")[:50]  # Limit to 50 results for performance
            )

    return render(
        request,
        "recipes/post/search.html",
        {
            "form": form,
            "query": query,
            "results": results,
            "search_method": search_method,
        },
    )


def feeling_hungry(request):
    total_posts = Post.published.count()
    if total_posts == 0:
        return redirect("recipes:post_list")

    random_index = random.randrange(total_posts)
    random_post = Post.published.all()[random_index]
    return redirect(random_post.get_absolute_url())
