import random

from django.core.cache import cache
from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Prefetch, Q
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
from .models import Comment, Post, RecipeIngredient
from .forms import CommentForm, SearchForm


PUBLISHED_POST_IDS_CACHE_KEY = "recipes.published_post_ids"
PUBLISHED_POST_IDS_CACHE_TIMEOUT = 60 * 15


def _get_cache_key(prefix, identifier):
    """Generate a consistent cache key."""
    return f"recipes.{prefix}.{identifier}"


def _recipe_queryset():
    return Post.published.select_related("author").prefetch_related("tags")


def _recipe_detail_queryset():
    return Post.published.select_related("author").prefetch_related(
        "tags",
        Prefetch(
            "recipe_ingredients",
            queryset=RecipeIngredient.objects.select_related("ingredient"),
        ),
        "recipe_steps",
        Prefetch("comments", queryset=Comment.objects.filter(active=True)),
    )


def _published_post_ids():
    return cache.get_or_set(
        PUBLISHED_POST_IDS_CACHE_KEY,
        lambda: list(Post.published.values_list("id", flat=True)),
        PUBLISHED_POST_IDS_CACHE_TIMEOUT,
    )


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
    post_qs = _recipe_queryset()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_qs = post_qs.filter(tags__in=[tag])
    
    # Cache the count of total posts for display
    cache_key = f"recipes.post_list_count.{tag_slug or 'all'}"
    total_count = cache.get_or_set(
        cache_key,
        lambda: post_qs.count(),
        60 * 5,  # 5 minutes
    )

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
        _recipe_detail_queryset(),
        slug=post,
        status=Post.Status.PUBLISHED,
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )
    # Display only active comments in chronological order
    comments = post.comments.all()
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

            # Try to get cached results first
            cache_key = _get_cache_key("search", query)
            results = cache.get(cache_key)
            
            if results is None:
                # Use basic database search with Q objects
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
                    _recipe_queryset().filter(q_objects)
                    .distinct()
                    .order_by("-publish")[:50]  # Limit to 50 results for performance
                )
                # Cache results for 10 minutes
                cache.set(cache_key, results, 60 * 10)

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
    published_post_ids = _published_post_ids()
    if not published_post_ids:
        return redirect("recipes:post_list")

    random_post_id = random.choice(published_post_ids)
    random_post = _recipe_queryset().get(pk=random_post_id)
    cache.set("recipes.last_random_post_id", random_post_id, 60 * 60)
    return redirect(random_post.get_absolute_url())
