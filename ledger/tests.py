from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import BankCard, Expense


class ExpenseFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='mike', password='pass12345')
        self.other_user = User.objects.create_user(username='alice', password='pass12345')
        self.card = BankCard.objects.create(
            user=self.user,
            name='Main Card',
            balance=Decimal('100.00'),
        )
        self.other_card = BankCard.objects.create(
            user=self.other_user,
            name='Other Card',
            balance=Decimal('100.00'),
        )
        self.client.force_login(self.user)

    def test_add_expense_deducts_card_balance(self):
        response = self.client.post(reverse('add_expense'), {
            'bank_card': self.card.pk,
            'amount': '25.50',
            'category': '餐饮',
            'note': 'lunch',
            'expense_date': date.today().isoformat(),
        })

        self.assertRedirects(response, reverse('dashboard'))
        self.card.refresh_from_db()
        self.assertEqual(self.card.balance, Decimal('74.50'))
        self.assertEqual(
            Expense.objects.get(user=self.user, bank_card=self.card).amount,
            Decimal('25.50'),
        )

    def test_add_expense_rejects_insufficient_balance(self):
        response = self.client.post(reverse('add_expense'), {
            'bank_card': self.card.pk,
            'amount': '150.00',
            'category': '购物',
            'note': '',
            'expense_date': date.today().isoformat(),
        })

        # 余额不足时表单仍有效，但视图渲染 dashboard 返回 200（保留表单数据）
        self.assertEqual(response.status_code, 200)
        self.card.refresh_from_db()
        self.assertEqual(self.card.balance, Decimal('100.00'))
        self.assertFalse(Expense.objects.filter(user=self.user).exists())

    def test_add_expense_rejects_other_users_card(self):
        response = self.client.post(reverse('add_expense'), {
            'bank_card': self.other_card.pk,
            'amount': '10.00',
            'category': '交通',
            'note': '',
            'expense_date': date.today().isoformat(),
        })

        # 表单无效（不是自己的卡），视图渲染 dashboard 返回 200
        self.assertEqual(response.status_code, 200)
        self.other_card.refresh_from_db()
        self.assertEqual(self.other_card.balance, Decimal('100.00'))
        self.assertFalse(Expense.objects.filter(user=self.user).exists())

    def test_delete_expense_restores_card_balance(self):
        expense = Expense.objects.create(
            user=self.user,
            bank_card=self.card,
            amount=Decimal('20.00'),
            category='娱乐',
            expense_date=date.today(),
        )
        self.card.balance = Decimal('80.00')
        self.card.save()

        response = self.client.post(reverse('delete_expense', args=[expense.pk]))

        self.assertRedirects(response, reverse('dashboard'))
        self.card.refresh_from_db()
        self.assertEqual(self.card.balance, Decimal('100.00'))
        self.assertFalse(Expense.objects.filter(pk=expense.pk).exists())

    def test_delete_bank_card_with_expenses_is_blocked(self):
        Expense.objects.create(
            user=self.user,
            bank_card=self.card,
            amount=Decimal('10.00'),
            category='其他',
            expense_date=date.today(),
        )

        response = self.client.post(reverse('delete_bank_card', args=[self.card.pk]))

        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(BankCard.objects.filter(pk=self.card.pk).exists())
