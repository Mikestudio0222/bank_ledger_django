from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from .models import BankCard, Expense
from .forms import UserRegisterForm, UserLoginForm, BankCardForm, ExpenseForm


def rate_limit(key_prefix, limit=5, period=60):
    """基于 IP 的简易请求频率限制。"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            client_ip = request.META.get(
                'HTTP_X_FORWARDED_FOR',
                request.META.get('REMOTE_ADDR', '127.0.0.1')
            ).split(',')[0].strip()
            cache_key = f'rl:{key_prefix}:{client_ip}'
            count = cache.get(cache_key, 0)
            if count >= limit:
                return HttpResponse('请求过于频繁，请稍后再试。', status=429)
            cache.set(cache_key, count + 1, period)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@rate_limit('register', limit=3, period=300)
def register_view(request):
    """用户注册（需邮箱验证）"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # 验证邮箱前禁止登录
            user.save()

            # 发送验证邮件
            signer = TimestampSigner()
            token = signer.sign(str(user.pk))
            verify_url = request.build_absolute_uri(
                reverse('verify_email', kwargs={'token': token})
            )
            send_mail(
                subject='验证你的邮箱 - 记账工具',
                message=(
                    f'Hi {user.username},\n\n'
                    f'请点击以下链接验证你的邮箱地址（24小时内有效）：\n\n'
                    f'{verify_url}\n\n'
                    f'如果这不是你注册的，请忽略此邮件。'
                ),
                from_email=None,  # 使用 DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(
                request,
                f'注册成功！验证邮件已发送到 {user.email}，请查收并点击链接激活账号。'
            )
            return redirect('login')
    else:
        form = UserRegisterForm()

    return render(request, 'ledger/register.html', {'form': form})


def verify_email(request, token):
    """邮箱验证"""
    signer = TimestampSigner()
    try:
        pk = signer.unsign(token, max_age=86400)  # 24 小时
        user = User.objects.get(pk=pk)
        if user.is_active:
            messages.info(request, '该账号已验证过，可以直接登录。')
        else:
            user.is_active = True
            user.save()
            messages.success(request, '邮箱验证成功！现在可以登录了。')
    except (BadSignature, SignatureExpired, User.DoesNotExist):
        messages.error(request, '验证链接无效或已过期（24小时），请重新注册。')

    return redirect('login')


@rate_limit('login', limit=10, period=60)
def login_view(request):
    """用户登录"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            return redirect('dashboard')
        # 检查是否是 inactive 用户（表单已通过认证但用户被禁）
        elif form.errors.get('__all__'):
            pass  # AuthenticationForm 会把 inactive 用户的错误放在 __all__
    else:
        form = UserLoginForm()

    return render(request, 'ledger/login.html', {'form': form})


def logout_view(request):
    """用户退出"""
    logout(request)
    messages.info(request, '您已成功退出登录。')
    return redirect('login')


def _get_dashboard_context(user, expense_form=None):
    """构建仪表盘页面的上下文数据"""
    bank_cards = BankCard.objects.filter(user=user)
    total_balance = bank_cards.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

    records = Expense.objects.filter(user=user).select_related('bank_card')

    today = timezone.now().date()
    month_start = today.replace(day=1)

    today_expenses = records.filter(expense_date=today, record_type='expense')
    today_expense_total = today_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    today_income = records.filter(expense_date=today, record_type='income')
    today_income_total = today_income.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    month_expenses = records.filter(expense_date__gte=month_start, record_type='expense')
    month_expense_total = month_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    month_income = records.filter(expense_date__gte=month_start, record_type='income')
    month_income_total = month_income.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    total_records = records.count()

    if expense_form is None:
        expense_form = ExpenseForm(user=user)

    return {
        'bank_cards': bank_cards,
        'total_balance': total_balance,
        'expenses': records[:20],
        'today_expense_total': today_expense_total,
        'today_income_total': today_income_total,
        'month_expense_total': month_expense_total,
        'month_income_total': month_income_total,
        'total_records': total_records,
        'expense_form': expense_form,
    }


@login_required
def dashboard_view(request):
    """仪表盘主页"""
    context = _get_dashboard_context(request.user)
    return render(request, 'ledger/dashboard.html', context)


def _card_json(card):
    """序列化银行卡为 JSON 友好格式"""
    return {
        'id': card.pk,
        'name': card.name,
        'balance': str(card.balance),
        'icon': card.icon,
    }


@login_required
def add_bank_card(request):
    """添加银行卡（支持 AJAX）"""
    if request.method == 'POST':
        form = BankCardForm(request.POST)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if form.is_valid():
            bank_card = form.save(commit=False)
            bank_card.user = request.user
            bank_card.save()
            if is_ajax:
                return JsonResponse({'success': True, 'card': _card_json(bank_card)})
            messages.success(request, '银行卡添加成功！')
            return redirect('dashboard')
        if is_ajax:
            errors = {f: [str(e) for e in errs] for f, errs in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        form = BankCardForm()

    return render(request, 'ledger/add_bank_card.html', {'form': form})


@login_required
def edit_bank_card(request, pk):
    """编辑银行卡（支持 AJAX）"""
    bank_card = get_object_or_404(BankCard, pk=pk, user=request.user)

    if request.method == 'POST':
        form = BankCardForm(request.POST, instance=bank_card)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if form.is_valid():
            form.save()
            bank_card.refresh_from_db()
            if is_ajax:
                return JsonResponse({'success': True, 'card': _card_json(bank_card)})
            messages.success(request, '银行卡修改成功！')
            return redirect('dashboard')
        if is_ajax:
            errors = {f: [str(e) for e in errs] for f, errs in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        form = BankCardForm(instance=bank_card)

    return render(request, 'ledger/edit_bank_card.html', {'form': form, 'bank_card': bank_card})


@login_required
def delete_bank_card(request, pk):
    """删除银行卡（支持 AJAX）"""
    bank_card = get_object_or_404(BankCard, pk=pk, user=request.user)
    expense_count = bank_card.expenses.count()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        if expense_count:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': '这张银行卡已有收支记录，请先删除相关记录后再删除银行卡。'
                }, status=400)
            messages.error(request, '这张银行卡已有收支记录，请先处理相关记录后再删除。')
            return redirect('dashboard')

        bank_card.delete()
        total = BankCard.objects.filter(user=request.user).aggregate(
            total=Sum('balance')
        )['total'] or Decimal('0.00')
        if is_ajax:
            return JsonResponse({'success': True, 'total_balance': str(total)})
        messages.success(request, '银行卡已删除！')
        return redirect('dashboard')

    return render(
        request,
        'ledger/delete_bank_card.html',
        {'bank_card': bank_card, 'expense_count': expense_count},
    )


@login_required
def add_expense(request):
    """添加收支记录"""
    if request.method != 'POST':
        return redirect('dashboard')

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    form = ExpenseForm(user=request.user, data=request.POST)

    if form.is_valid():
        amount = form.cleaned_data['amount']
        record_type = form.cleaned_data['record_type']

        with transaction.atomic():
            bank_card = BankCard.objects.select_for_update().get(
                pk=form.cleaned_data['bank_card'].pk,
                user=request.user,
            )

            if record_type == 'expense' and bank_card.balance < amount:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': '余额不足！'}, status=400)
                messages.error(request, '余额不足！')
                context = _get_dashboard_context(request.user, expense_form=form)
                return render(request, 'ledger/dashboard.html', context)

            expense = form.save(commit=False)
            expense.user = request.user
            expense.bank_card = bank_card

            if record_type == 'expense':
                bank_card.balance -= amount
            else:
                bank_card.balance += amount
            bank_card.save(update_fields=['balance', 'updated_at'])
            expense.save()

        if is_ajax:
            today = timezone.now().date()
            month_start = today.replace(day=1)
            user_records = Expense.objects.filter(user=request.user)
            return JsonResponse({
                'success': True,
                'record_type': record_type,
                'balance': str(bank_card.balance),
                'total_balance': str(
                    BankCard.objects.filter(user=request.user).aggregate(
                        total=Sum('balance')
                    )['total'] or Decimal('0.00')
                ),
                'today_expense_total': str(user_records.filter(
                    expense_date=today, record_type='expense'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')),
                'today_income_total': str(user_records.filter(
                    expense_date=today, record_type='income'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')),
                'month_expense_total': str(user_records.filter(
                    expense_date__gte=month_start, record_type='expense'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')),
                'month_income_total': str(user_records.filter(
                    expense_date__gte=month_start, record_type='income'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')),
                'total_records': user_records.count(),
            })
        messages.success(request, '记账成功！')
        return redirect('dashboard')

    # Form invalid
    if is_ajax:
        errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    messages.error(request, '记账失败，请检查表单内容。')
    context = _get_dashboard_context(request.user, expense_form=form)
    return render(request, 'ledger/dashboard.html', context)


@login_required
def delete_expense(request, pk):
    """删除收支记录（支持 AJAX）"""
    expense = get_object_or_404(
        Expense.objects.select_related('bank_card'),
        pk=pk,
        user=request.user,
    )
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        with transaction.atomic():
            expense = get_object_or_404(
                Expense.objects.select_for_update(),
                pk=pk,
                user=request.user,
            )
            bank_card = BankCard.objects.select_for_update().get(
                pk=expense.bank_card_id,
                user=request.user,
            )

            # 恢复余额：支出则加回，收入则扣除
            if expense.record_type == 'expense':
                bank_card.balance += expense.amount
            else:
                bank_card.balance -= expense.amount
            bank_card.save(update_fields=['balance', 'updated_at'])
            expense.delete()

        if is_ajax:
            today = timezone.now().date()
            month_start = today.replace(day=1)
            user_records = Expense.objects.filter(user=request.user)
            return JsonResponse({
                'success': True,
                'card_id': bank_card.pk,
                'balance': str(bank_card.balance),
                'total_balance': str(
                    BankCard.objects.filter(user=request.user).aggregate(
                        total=Sum('balance')
                    )['total'] or Decimal('0.00')
                ),
                'today_expense_total': str(user_records.filter(
                    expense_date=today, record_type='expense'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')),
                'today_income_total': str(user_records.filter(
                    expense_date=today, record_type='income'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')),
                'month_expense_total': str(user_records.filter(
                    expense_date__gte=month_start, record_type='expense'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')),
                'month_income_total': str(user_records.filter(
                    expense_date__gte=month_start, record_type='income'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')),
                'total_records': user_records.count(),
            })

        messages.success(request, '记录已删除，余额已恢复！')
        return redirect('dashboard')

    return render(request, 'ledger/delete_expense.html', {'expense': expense})


@login_required
def expenses_list(request):
    """收支记录列表（支持无限滚动 AJAX）"""
    expenses = Expense.objects.filter(user=request.user).select_related('bank_card')

    category = request.GET.get('category')
    if category:
        expenses = expenses.filter(category=category)

    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        items = [{
            'id': e.pk,
            'category': e.category,
            'amount': str(e.amount),
            'record_type': e.record_type,
            'bank_card_name': e.bank_card.name,
            'note': e.note or '',
            'expense_date': str(e.expense_date),
            'delete_url': f'/expenses/{e.pk}/delete/',
        } for e in page_obj]
        return JsonResponse({
            'items': items,
            'has_next': page_obj.has_next(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        })

    context = {
        'page_obj': page_obj,
        'categories': Expense.CATEGORY_CHOICES,
        'selected_category': category,
    }

    return render(request, 'ledger/expenses_list.html', context)
