from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticazione (usiamo le viste built-in di Django)
    path('', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # App views
    path('dashboard/', views.dashboard, name='dashboard'),
    path('session/create/', views.create_session, name='create_session'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('register/', views.register, name='register'),
    path('set/<int:set_id>/delete/', views.delete_set, name='delete_set'),
    path('set/<int:set_id>/duplicate/', views.duplicate_set, name='duplicate_set'),
    path('set/<int:set_id>/edit/', views.edit_set, name='edit_set'),
    path('session/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('session/<int:session_id>/duplicate/', views.duplicate_session, name='duplicate_session'),
    path('session/<int:session_id>/edit-date/', views.edit_session_date, name='edit_session_date'),
    path('session/<int:session_id>/delete-exercise/<int:exercise_id>/', views.delete_exercise_sets, name='delete_exercise_sets'),
    path('session/<int:session_id>/reorder/', views.reorder_exercises, name='reorder_exercises'),
    path('exercises/suggestions/', views.exercise_suggestions, name='exercise_suggestions'),
]
