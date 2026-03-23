from django import forms

from .models import Comment


# Comment form used on post detail pages
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["name", "email", "body"]


# Search form for searching recipes
class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=250,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search recipes...",
                "class": "search-input-dynamic"
            }
        ),
    )
