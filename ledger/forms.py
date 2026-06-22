from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import BankCard, Expense


class UserRegisterForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': '邮箱地址'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '用户名'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': '密码'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': '确认密码'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserLoginForm(AuthenticationForm):
    """用户登录表单"""
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '用户名'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': '密码'
    }))


class BankCardForm(forms.ModelForm):
    """银行卡表单"""
    class Meta:
        model = BankCard
        fields = ['name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：工商银行'
            }),
            'icon': forms.HiddenInput()
        }


class ExpenseForm(forms.ModelForm):
    """消费记录表单"""
    class Meta:
        model = Expense
        fields = ['bank_card', 'amount', 'category', 'note', 'expense_date']
        widgets = {
            'bank_card': forms.Select(attrs={
                'class': 'form-select'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'note': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '添加备注（可选）'
            }),
            'expense_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields['bank_card'].queryset = BankCard.objects.filter(user=user)
        else:
            self.fields['bank_card'].queryset = BankCard.objects.none()

    def clean_bank_card(self):
        bank_card = self.cleaned_data.get('bank_card')
        if bank_card is None:
            return bank_card
        if self.user and bank_card.user_id != self.user.id:
            raise forms.ValidationError('请选择自己的银行卡。')
        return bank_card
