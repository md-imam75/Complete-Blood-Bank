from django.urls import path
from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('', views.home, name='home'), 
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(template_name='blood/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('search-donors/', views.search_donors, name='search_donors'),
    path('request-blood/', views.create_blood_request, name='create_blood_request'),
    path('approve-request/<int:pk>/', views.approve_blood_request, name='approve_blood_request'),
    path('approve-donation/<int:pk>/', views.admin_approve_donation, name='admin_approve_donation'),
    path('reject-donation/<int:pk>/', views.admin_reject_donation, name='admin_reject_donation'),
    
    path('manage/request/reject/<int:pk>/', views.reject_blood_request, name='reject_blood_request'),
    path('admin-control/generate-report/', views.generate_report_pdf, name='generate_report_pdf'),

    path('profile/', views.profile_management, name='profile'),
    path('emergency-feed/', views.emergency_feed, name='emergency_feed'),
    path('emergency-post/new/', views.create_emergency_post, name='create_emergency_post'),
    path('add-comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('mark-managed/<int:post_id>/', views.mark_managed, name='mark_managed'),
    
    path('request-history/', views.request_history, name='request_history'),
    
    path('donate/request/', views.create_donation_request, name='create_donation_request'),
    
    
    path('admin-control/donation-history/', views.admin_donation_history, name='admin_donation_history'),
    path('admin-control/blood-request-history/', views.admin_blood_request_history, name='admin_blood_request_history'),
]