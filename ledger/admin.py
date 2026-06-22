from django.contrib import admin
from .models import BankCard, Expense


@admin.register(BankCard)
class BankCardAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'balance', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['user', 'bank_card', 'amount', 'category', 'expense_date', 'created_at']
    list_filter = ['category', 'expense_date', 'user']
    search_fields = ['note', 'user__username']
    readonly_fields = ['created_at']
    date_hierarchy = 'expense_date'
