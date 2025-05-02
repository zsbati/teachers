from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.utils import timezone
from .models import Teacher, CustomUser, Task, WorkSession, SalaryReport, Student, Service
from .billing_models import BillItem


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
        fields = ['name', 'description', 'hourly_rate', 'price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class WorkSessionManualForm(forms.ModelForm):
    class Meta:
        model = WorkSession
        fields = ['task', 'manual_hours', 'student']
        widgets = {
            'task': forms.Select(attrs={'class': 'form-control'}),
            'manual_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'student': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manual_hours'].label = 'Hours Worked'
        self.fields['student'].queryset = Student.objects.all()  
        print("Student widget in WorkSessionManualForm:", type(self.fields['student'].widget))

    def clean(self):
        cleaned_data = super().clean()
        manual_hours = cleaned_data.get('manual_hours')
        # Accept 0 as a valid value, but not None or empty
        if manual_hours in (None, ''):
            raise forms.ValidationError('Manual entry type requires manual_hours')
        try:
            if float(manual_hours) < 0:
                raise forms.ValidationError('Manual hours cannot be negative')
        except (TypeError, ValueError):
            raise forms.ValidationError('Manual hours must be a number')
        return cleaned_data


class WorkSessionClockForm(forms.ModelForm):
    class Meta:
        model = WorkSession
        fields = ['task', 'student']
        widgets = {
            'task': forms.Select(attrs={'class': 'form-control'}),
            'student': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.all()
        print("Student widget in WorkSessionClockForm:", type(self.fields['student'].widget))

class WorkSessionTimeRangeForm(forms.ModelForm):
    class Meta:
        model = WorkSession
        fields = ['task', 'start_time', 'end_time', 'student']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'student': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.all()
        print("Student widget in WorkSessionTimeRangeForm:", type(self.fields['student'].widget))

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

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        if username and CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")

        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")

        return cleaned_data


class ChangeTeacherPasswordForm(forms.Form):
    new_password = forms.CharField(
        required=True,
        label="New Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    confirm_password = forms.CharField(
        required=True,
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

class ChangeStudentPasswordForm(forms.Form):
    new_password = forms.CharField(
        required=True,
        label="New Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def save(self, user):
        user.set_password(self.cleaned_data['new_password'])
        user.save()


class StudentCreationForm(UserCreationForm):
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the password confirmation field
        self.fields.pop('password2')

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class EditStudentForm(forms.ModelForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Student
        fields = ['phone', 'is_active']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            # Initialize form fields with current values
            self.initial['phone'] = self.instance.phone
            self.initial['is_active'] = self.instance.is_active
            # Try to get email from user if it exists
            try:
                self.initial['email'] = self.instance.user.email
            except CustomUser.DoesNotExist:
                self.initial['email'] = ''

    def save(self, commit=True):
        student = super().save(commit=False)
        if self.instance and self.instance.user:
            # Update user's email if it changed
            current_email = self.instance.user.email
            new_email = self.cleaned_data.get('email', current_email)
            if new_email != current_email:
                self.instance.user.email = new_email
                self.instance.user.save()
        if commit:
            student.save()
        return student


class SalaryReportForm(forms.Form):
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        required=True,
        label="Teacher",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    year = forms.IntegerField(
        required=True,
        label="Year",
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    month = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 13)],
        required=True,
        label="Month",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    notes = forms.CharField(
        required=False,
        label="Notes",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values to current year and month
        self.initial['year'] = timezone.now().year
        self.initial['month'] = timezone.now().month


class BillItemForm(forms.ModelForm):
    """Form for adding services to a bill"""
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True),
        empty_label="Select a service...",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the service to add to the bill"
    )
    
    class Meta:
        model = BillItem
        fields = ['service', 'quantity', 'service_description']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'service_description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text
        self.fields['quantity'].help_text = 'Number of times this service was provided'
        self.fields['service_description'].help_text = 'Optional description for this service item'

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        quantity = cleaned_data.get('quantity')
        
        if service and quantity:
            # Calculate amount based on service price and quantity
            service_price = service.price
            cleaned_data['amount'] = service_price * quantity
            cleaned_data['service_name'] = service.name
            cleaned_data['service_description'] = service.description if service.description else ''
            cleaned_data['service_price_at_billing'] = service_price
            
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        service = self.cleaned_data.get('service')
        quantity = self.cleaned_data.get('quantity')
        if service and quantity:
            instance.service_price_at_billing = service.price
            instance.amount = service.price * quantity
            instance.service_name = service.name
            instance.service_description = service.description or ''
        if commit:
            instance.save()
        return instance


class InspectorCreationForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        from .models import CustomUser
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        if username and CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        if email:
            if CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError("Email already exists")
        return cleaned_data
