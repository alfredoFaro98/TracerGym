from django.contrib import admin
from .models import Tag, Exercise, ExerciseImage, WorkoutSession, WorkoutSet, WeekdayPlan, DayPlanOverride

admin.site.register(Tag)


class ExerciseImageInline(admin.TabularInline):
    model = ExerciseImage
    extra = 0


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipologia', 'target_muscle', 'origine')
    list_filter = ('origine', 'tags')
    search_fields = ('nome', 'target_muscle')
    inlines = [ExerciseImageInline]

class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 1

@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('utente', 'data')
    list_filter = ('data', 'utente')
    inlines = [WorkoutSetInline]


@admin.register(WeekdayPlan)
class WeekdayPlanAdmin(admin.ModelAdmin):
    list_display = ('utente', 'giorno_settimana', 'tag', 'riposo')
    list_filter = ('utente', 'giorno_settimana')


@admin.register(DayPlanOverride)
class DayPlanOverrideAdmin(admin.ModelAdmin):
    list_display = ('utente', 'data', 'tag', 'riposo')
    list_filter = ('utente', 'data')
