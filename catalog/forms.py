from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from .models import Genre, Language
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

## Create from fields with this file
## The declaration syntax for a Form is very similar
## to that for declaring a Model, and shares the same field types (and some similar parameters).

class AddBookForm(forms.Form):
    book_title = forms.CharField(min_length=3, max_length=200,
                                 widget= forms.TextInput(attrs={"placeholder":"Enter Book Title", "class":"form-control"}))
    author_firstname = forms.CharField(max_length=50,
                                       widget= forms.TextInput(attrs={"placeholder":"First Name", "class":"form-control"}))
    author_lastname = forms.CharField(max_length=50,
                                      widget= forms.TextInput(attrs={"placeholder":"Last Name", "class":"form-control"}))
    summary = forms.CharField(max_length=1000,
                              widget=forms.Textarea(attrs={"placeholder":"Enter a brief description of the book", "class":"form-control"}))
    isbn = forms.CharField(max_length=13,
                          widget = forms.TextInput(attrs={"placeholder":"13 Character ISBN No", "class":"form-control"}),
                          help_text='<a href="https://www.isbn-international.org/content/what-isbn">ISBN number</a>', required=True)
    genre = forms.ModelMultipleChoiceField(queryset=Genre.objects.all(),widget=forms.widgets.CheckboxSelectMultiple())
    language = forms.ModelChoiceField(queryset=Language.objects.all(), empty_label="Select a Language")
    def clean_book_title(self):
        data = self.cleaned_data['book_title']
        # raise ValidationError( _("Test Error"))
        # print(data)
        return data

class SignUpForm(UserCreationForm):
# class SignUpForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True,
                                widget= forms.TextInput(attrs={"placeholder":"First Name", "class":"form-control"}))
    last_name = forms.CharField(max_length=30, required=True,
                                widget= forms.TextInput(attrs={"placeholder":"Last Name", "class":"form-control"}))
    email = forms.EmailField(max_length=254,required=False,
                            widget=forms.EmailInput(attrs={"placeholder":"Enter Your Email", "class":"form-control"}))
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput()
        self.fields["username"].help_text = []
        self.fields['username'].widget.attrs = {'class': 'form-control',"placeholder":"Enter username"}
        self.fields['password1'].widget.attrs = {'class': 'form-control',}
        self.fields['password1'].help_text = ["Your password must contain at least 8 characters.","Your password can’t be entirely numeric."]
        self.fields['password2'].widget.attrs = {'class': 'form-control',}
        self.fields['password2'].help_text = ["Enter the same password as before, for verification."]
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )
        labels = {
                    'first_name': "First Name",
                    'last_name':"Last Name",
                }
