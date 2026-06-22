from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class BankCard(models.Model):
    """银行卡模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_cards', db_index=True, verbose_name='用户')
    name = models.CharField(max_length=100, verbose_name='卡名')
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='余额'
    )
    icon = models.CharField(max_length=50, default='fa-credit-card', verbose_name='图标')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'bank_cards'
        verbose_name = '银行卡'
        verbose_name_plural = '银行卡'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Expense(models.Model):
    """收支记录模型"""
    TYPE_CHOICES = [
        ('expense', '支出'),
        ('income', '收入'),
    ]

    CATEGORY_CHOICES = [
        ('餐饮', '🍜 餐饮'),
        ('购物', '🛍️ 购物'),
        ('交通', '🚗 交通'),
        ('娱乐', '🎮 娱乐'),
        ('医疗', '💊 医疗'),
        ('教育', '📚 教育'),
        ('住房', '🏠 住房'),
        ('薪资', '💰 薪资'),
        ('其他', '📦 其他'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses', verbose_name='用户')
    bank_card = models.ForeignKey(BankCard, on_delete=models.CASCADE, related_name='expenses', verbose_name='银行卡')
    record_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='expense', db_index=True, verbose_name='类型')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='金额'
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True, verbose_name='分类')
    note = models.CharField(max_length=200, blank=True, verbose_name='备注')
    expense_date = models.DateField(db_index=True, verbose_name='日期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'expenses'
        verbose_name = '收支记录'
        verbose_name_plural = '收支记录'
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        sign = '-' if self.record_type == 'expense' else '+'
        return f"{self.user.username} - {self.category} - {sign}¥{self.amount}"
