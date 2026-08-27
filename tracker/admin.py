from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.shortcuts import render
from .models import Tag, Exercise, ExerciseImage, WorkoutSession, WorkoutSet, WeekdayPlan, DayPlanOverride

admin.site.register(Tag)


class HasLuogoFilter(admin.SimpleListFilter):
    title = 'sede'
    parameter_name = 'has_luogo'

    def lookups(self, request, model_admin):
        return (('no', 'Senza sede'), ('si', 'Con sede'))

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(luogo='')
        if self.value() == 'si':
            return queryset.exclude(luogo='')
        return queryset


class SetLuogoForm(forms.Form):
    luogo = forms.CharField(label='Sede', max_length=150)


@admin.action(description='Imposta sede sulle sessioni selezionate (solo le tue)')
def set_luogo(modeladmin, request, queryset):
    """Riempie il campo 'luogo' sulle sessioni selezionate. Per sicurezza
    opera solo sulle sessioni dell'utente che lancia l'azione, anche se
    nella selezione ci fossero sessioni di altri utenti."""
    queryset = queryset.filter(utente=request.user)
    form = None
    if 'apply' in request.POST:
        form = SetLuogoForm(request.POST)
        if form.is_valid():
            count = queryset.update(luogo=form.cleaned_data['luogo'])
            modeladmin.message_user(request, f'Sede impostata su {count} sessioni.', messages.SUCCESS)
            return None
    if form is None:
        form = SetLuogoForm()
    return render(request, 'admin/set_luogo_confirmation.html', {
        'sessions': queryset,
        'form': form,
        'action_checkbox_name': ACTION_CHECKBOX_NAME,
        'opts': WorkoutSession._meta,
    })


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
    list_display = ('utente', 'data', 'luogo')
    list_filter = ('data', 'utente', HasLuogoFilter)
    actions = [set_luogo]
    inlines = [WorkoutSetInline]


@admin.register(WeekdayPlan)
class WeekdayPlanAdmin(admin.ModelAdmin):
    list_display = ('utente', 'giorno_settimana', 'tag', 'riposo')
    list_filter = ('utente', 'giorno_settimana')


@admin.register(DayPlanOverride)
class DayPlanOverrideAdmin(admin.ModelAdmin):
    list_display = ('utente', 'data', 'tag', 'riposo')
    list_filter = ('utente', 'data')
