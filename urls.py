from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('apply_pass_instruction/', views.apply_pass_instruction, name='apply_pass_instruction'),
    path('apply_pass_form/', views.apply_pass_form, name='apply_pass_form'),
    path('payment/', views.payment_view, name='payment'),
    path('view_user_pass/', views.view_user_pass, name='view_user_pass'),
    path('download_pass/', views.download_pass, name='download_pass'),
    path('auth_dashboard/', views.auth_dashboard, name='auth_dashboard'),
    path('update_pass_status/<int:pass_id>/<str:status>/', views.update_pass_status, name='update_pass_status'),
    path('view_all_passes/', views.view_all_passes, name='view_all_passes'),
    path('export_passes/', views.export_passes, name='export_passes'),
    path('export_pass_data/<str:format>/', views.export_pass_data, name='export_pass_data'),
    path('generate_pdf_pass/<int:pass_id>/', views.generate_pdf_pass, name='generate_pdf_pass'),
]
