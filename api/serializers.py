from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Todo, Session, Segment, Profile
from django.utils import timezone

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('zen_mode_audio_enabled', 'ai_enabled', 'ai_provider', 'ollama_url', 'ollama_model', 'groq_api_key', 'groq_model', 'settings_json')

class UserSerializer(serializers.ModelSerializer):
    current_streak = serializers.SerializerMethodField()
    total_focus_minutes = serializers.SerializerMethodField()
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'current_streak', 'total_focus_minutes', 'profile')

    def get_current_streak(self, obj):
        from datetime import date, timedelta
        # Get all dates with at least one focus segment
        segments = Segment.objects.filter(
            session__user=obj, 
            mode='focus'
        ).values_list('start_at', flat=True)
        
        # Convert timestamps to distinct dates
        active_dates = set(dt.date() for dt in segments)
        
        if not active_dates:
            return 0
            
        today = timezone.now().date()
        streak = 0
        
        # Check if user focused today or yesterday to keep streak alive
        if today in active_dates:
            streak = 1
            check_date = today - timedelta(days=1)
        elif (today - timedelta(days=1)) in active_dates:
            streak = 0 # Will verify yesterday in loop or just start checking from yesterday
            check_date = today - timedelta(days=1)
        else:
            return 0

        while check_date in active_dates:
            streak += 1
            check_date -= timedelta(days=1)
            
        return streak

    def get_total_focus_minutes(self, obj):
        segments = Segment.objects.filter(
            session__user=obj, 
            mode='focus', 
            end_at__isnull=False
        )
        total_seconds = 0
        for seg in segments:
            total_seconds += (seg.end_at - seg.start_at).total_seconds()
        
        return int(total_seconds / 60)

class SegmentSerializer(serializers.ModelSerializer):
    segment_duration_seconds = serializers.SerializerMethodField()
    session_todo_id = serializers.SerializerMethodField()

    class Meta:
        model = Segment
        fields = (
            'id', 'session', 'mode', 'start_at', 'end_at', 
            'reason', 'created_at', 'segment_duration_seconds',
            'session_todo_id'
        )

    def get_segment_duration_seconds(self, obj):
        if obj.start_at and obj.end_at:
            return int((obj.end_at - obj.start_at).total_seconds())
        elif obj.start_at and not obj.end_at:
            return int((timezone.now() - obj.start_at).total_seconds())
        return 0

    def get_session_todo_id(self, obj):
        return obj.session.todo.id if obj.session and obj.session.todo else None

class SessionSerializer(serializers.ModelSerializer):
    segments = SegmentSerializer(many=True, read_only=True)
    session_total_focus_seconds = serializers.SerializerMethodField()
    session_total_pause_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = (
            'id', 'user', 'todo', 'created_at', 'ended_at', 
            'status', 'segments', 'session_total_focus_seconds', 
            'session_total_pause_seconds'
        )

    def get_session_total_focus_seconds(self, obj):
        segments = obj.segments.filter(mode='focus')
        total = 0
        for seg in segments:
            if seg.start_at and seg.end_at:
                total += (seg.end_at - seg.start_at).total_seconds()
            elif seg.start_at and not seg.end_at:
                total += (timezone.now() - seg.start_at).total_seconds()
        return int(total)

    def get_session_total_pause_seconds(self, obj):
        # pause + break
        segments = obj.segments.filter(mode__in=['pause', 'break'])
        total = 0
        for seg in segments:
            if seg.start_at and seg.end_at:
                total += (seg.end_at - seg.start_at).total_seconds()
            elif seg.start_at and not seg.end_at:
                total += (timezone.now() - seg.start_at).total_seconds()
        return int(total)

class TodoSerializer(serializers.ModelSerializer):
    sessions = SessionSerializer(many=True, read_only=True)
    past_focus_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Todo
        fields = (
            'id', 'user', 'title', 'description', 'priority', 
            'estimated_minutes', 'tags', 'created_at', 'updated_at', 
            'completed_at', 'sessions', 'past_focus_seconds'
        )
        read_only_fields = ('user',)

    def get_past_focus_seconds(self, obj):
        # Calculate sum of all closed focus segments across all sessions
        # Open segments (current focus) are excluded so frontend can add live timer
        total = 0
        for session in obj.sessions.all():
            for seg in session.segments.all():
                if seg.mode == 'focus' and seg.end_at and seg.start_at:
                    total += (seg.end_at - seg.start_at).total_seconds()
        return int(total)
