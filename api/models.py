import uuid
from django.db import models
from django.contrib.auth.models import User

class Todo(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('med', 'Medium'),
        ('high', 'High'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='med')
    estimated_minutes = models.PositiveIntegerField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

class Session(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('ended', 'Ended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"Session for {self.todo.title} ({self.status})"

class Segment(models.Model):
    MODE_CHOICES = [
        ('focus', 'Focus'),
        ('pause', 'Pause'),
        ('break', 'Break'),
    ]
    REASON_CHOICES = [
        ('idle', 'Idle'),
        ('hidden', 'Hidden'),
        ('manual', 'Manual'),
        ('alert', 'Alert'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='segments')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(blank=True, null=True)
    reason = models.CharField(max_length=10, choices=REASON_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mode} segment for session {self.session_id}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    zen_mode_audio_enabled = models.BooleanField(default=False)
    ai_enabled = models.BooleanField(default=False)
    ai_provider = models.CharField(max_length=10, choices=[('ollama', 'Ollama'), ('groq', 'Groq')], default='ollama')
    ollama_url = models.CharField(max_length=255, default="http://localhost:11434")
    ollama_model = models.CharField(max_length=255, default="qwen2.5-coder:1.5b")
    groq_api_key = models.CharField(max_length=255, blank=True, null=True)
    groq_model = models.CharField(max_length=255, default="llama-3.3-70b-versatile")
    
    # Generic settings blob for future-proofing
    settings_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"
