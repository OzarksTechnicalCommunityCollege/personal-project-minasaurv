from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Comment, Post


class CommentAuthTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="pass12345",
            first_name="Google",
            last_name="User",
        )
        self.post = Post.objects.create(
            title="Test Recipe",
            slug="test-recipe",
            author=self.user,
            content="Recipe content",
            publish=timezone.now(),
            status=Post.Status.PUBLISHED,
        )
        self.comment_url = reverse("recipes:post_comment", args=[self.post.id])

    def test_anonymous_user_redirected_for_comment_post(self):
        response = self.client.post(
            self.comment_url,
            {
                "body": "Nice recipe!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(Comment.objects.count(), 0)

    def test_authenticated_user_can_post_comment(self):
        self.client.login(username="tester", password="pass12345")
        response = self.client.post(
            self.comment_url,
            {
                "body": "Love this!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.name, "Google User")
        self.assertEqual(comment.email, "tester@example.com")
