from django.urls import path
from . import views

urlpatterns = [
    # 认证相关
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),

    # 银行卡管理
    path('cards/add/', views.add_bank_card, name='add_bank_card'),
    path('cards/<int:pk>/edit/', views.edit_bank_card, name='edit_bank_card'),
    path('cards/<int:pk>/delete/', views.delete_bank_card, name='delete_bank_card'),

    # 消费记录
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/<int:pk>/delete/', views.delete_expense, name='delete_expense'),
    path('expenses/', views.expenses_list, name='expenses_list'),
]
