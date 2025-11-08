from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

class SignupForm(UserCreationForm):
    username = forms.CharField(required=True, label="username", max_length=30, widget=forms.TextInput(attrs={"autocomplete": "username"}))
    email = forms.EmailField(required=True, label="Email", max_length=254, widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    password1 = forms.CharField(required=True, label="Mot de passe", max_length=30, widget=forms.PasswordInput)
    password2 = forms.CharField(required=True, label="Confirmer le mot de passe", max_length=30, widget=forms.PasswordInput)


    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            client_group, _ = Group.objects.get_or_create(name="Client")
            client_group.user_set.add(user)
        return user    