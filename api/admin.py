from django.contrib import admin
from .models import Todo, Session, Segment

@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'priority', 'completed_at')
    list_filter = ('priority', 'completed_at')
    search_fields = ('title', 'description')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('todo', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')

@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ('session', 'mode', 'reason', 'start_at', 'end_at')
    list_filter = ('mode', 'reason', 'start_at')
