from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import Teacher, CustomUser, Task, WorkSession


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class TeacherCreationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    subjects = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional: e.g., Math, Physics, Chemistry'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        if username and CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")

        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")

        return cleaned_data


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'hourly_rate', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class WorkSessionManualForm(forms.ModelForm):
    class Meta:
        model = WorkSession
        fields = ['task', 'manual_hours']
        widgets = {
            'task': forms.Select(attrs={'class': 'form-control'}),
            'manual_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manual_hours'].label = 'Hours Worked'


class WorkSessionClockForm(forms.ModelForm):
    class Meta:
        model = WorkSession
        fields = ['task']
        widgets = {
            'task': forms.Select(attrs={'class': 'form-control'}),
        }


class WorkSessionTimeRangeForm(forms.ModelForm):
    class Meta:
        model = WorkSession
        fields = ['task', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class WorkSessionFilterForm(forms.Form):
    """
    Form for filtering recent work sessions.
    """
    task = forms.ModelChoiceField(queryset=Task.objects.all(), required=False, label="Task")
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label="Start Date")
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label="End Date")


class AddTeacherForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Username",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        required=True,
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    subjects = forms.CharField(
        max_length=200,
        required=False,
        label="Subjects",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Optional: List of subjects taught"
    )
