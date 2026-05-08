from django.contrib import admin
from .models import Tag, Exercise, WorkoutSession, WorkoutSet

admin.site.register(Tag)
admin.site.register(Exercise)

class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 1

@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('utente', 'data')
    list_filter = ('data', 'utente')
    inlines = [WorkoutSetInline]
