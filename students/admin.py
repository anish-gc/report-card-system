from django.contrib import admin
from .models import Student, Subject, ReportCard, Mark

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'date_of_birth', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('name', 'email', 'date_of_birth', 'is_active')}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('code',)
    readonly_fields = ('created_at', 'updated_at')

class MarkInline(admin.TabularInline):
    model = Mark
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('subject', 'score', 'remarks', 'is_active')

class ReportCardAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'year', 'total_subjects', 'average_score', 'is_active')
    list_filter = ('term', 'year', 'is_active')
    search_fields = ('student__name', 'student__email')
    ordering = ('-year', '-term', 'student__name')
    readonly_fields = ('created_at', 'updated_at', 'total_subjects', 'average_score', 'total_score')
    inlines = [MarkInline]
    fieldsets = (
        (None, {'fields': ('student', 'term', 'year', 'is_active')}),
        ('Scores', {'fields': ('total_subjects', 'average_score', 'total_score')}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

class MarkAdmin(admin.ModelAdmin):
    list_display = ('report_card', 'subject', 'score', 'is_passing', 'is_active')
    list_filter = ('is_active', 'subject', 'report_card__term', 'report_card__year')
    search_fields = ('report_card__student__name', 'subject__name', 'subject__code')
    readonly_fields = ('created_at', 'updated_at', 'is_passing', 'percentage')
    fieldsets = (
        (None, {'fields': ('report_card', 'subject', 'score', 'remarks', 'is_active')}),
        ('Calculated Fields', {'fields': ('is_passing', 'percentage')}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

  
admin.site.register(Student, StudentAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(ReportCard, ReportCardAdmin)
admin.site.register(Mark, MarkAdmin)