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
    path('exercises/', views.exercises_list, name='exercises_list'),

    path('exercises/add/', views.add_exercise, name='add_exercise'),
    path('exercises/<int:exercise_id>/edit/', views.edit_exercise_admin, name='edit_exercise_admin'),
    path('exercises/<int:exercise_id>/delete/', views.delete_exercise_admin, name='delete_exercise_admin'),
    path('exercises/suggestions/', views.exercise_suggestions, name='exercise_suggestions'),
    path('exercises/export/', views.export_exercises_json, name='export_exercises_json'),
    path('session/<int:session_id>/export/', views.export_session, name='export_session'),
    path('export/', views.export_sessions, name='export_sessions'),
    path('import/', views.import_sessions, name='import_sessions'),
    path('users/', views.user_list, name='user_list'),
    path('users/<str:username>/', views.user_profile, name='user_profile'),
    path('users/<str:username>/session/<int:session_id>/', views.session_view, name='session_view'),
    path('profile/toggle-visibility/', views.toggle_profile_visibility, name='toggle_profile_visibility'),
    path('body-map/', views.body_map, name='body_map'),
]
