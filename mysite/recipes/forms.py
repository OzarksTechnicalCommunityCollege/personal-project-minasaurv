from django import forms

from .models import Comment


# Comment form used on post detail pages
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'email', 'body']