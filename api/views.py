from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Todo, Session, Segment
from .serializers import TodoSerializer, SessionSerializer, SegmentSerializer, UserSerializer

# Auth Views
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        user = User.objects.create_user(
            username=self.request.data['username'],
            email=self.request.data.get('email', ''),
            password=self.request.data['password']
        )
        serializer.instance = user

class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    def get_object(self):
        return self.request.user

class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Todo Views
class TodoListCreateView(generics.ListCreateAPIView):
    serializer_class = TodoSerializer
    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TodoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TodoSerializer
    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user)

# Session Views
class SessionStartView(APIView):
    def post(self, request):
        todo_id = request.data.get('todo_id')
        if not todo_id:
            return Response({"error": "todo_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            todo = Todo.objects.get(id=todo_id, user=request.user)
        except Todo.DoesNotExist:
            return Response({"error": "Todo not found"}, status=status.HTTP_404_NOT_FOUND)

        # Constraint: Only 1 active session per user
        active_sessions = Session.objects.filter(user=request.user, status='active')
        if active_sessions.exists():
            return Response({"error": "Another session is already active"}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        session = Session.objects.create(user=request.user, todo=todo, created_at=now, status='active')
        
        # Create first focus segment
        Segment.objects.create(session=session, mode='focus', start_at=now)
        
        return Response(SessionSerializer(session).data, status=status.HTTP_201_CREATED)

class SessionActiveView(APIView):
    def get(self, request):
        try:
            session = Session.objects.get(user=request.user, status='active')
            return Response(SessionSerializer(session).data)
        except Session.DoesNotExist:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

class SessionTransitionView(APIView):
    def post(self, request, pk):
        try:
            session = Session.objects.get(id=pk, user=request.user, status='active')
        except Session.DoesNotExist:
            return Response({"error": "Active session not found"}, status=status.HTTP_404_NOT_FOUND)

        mode = request.data.get('mode')
        reason = request.data.get('reason', 'manual')

        if mode not in ['focus', 'pause', 'break']:
            return Response({"error": "Invalid mode"}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        
        # Close open segments
        open_segments = Segment.objects.filter(session=session, end_at__isnull=True)
        if not open_segments.exists():
             return Response({"error": "No open segment found to transition from"}, status=status.HTTP_400_BAD_REQUEST)
        
        open_segments.update(end_at=now)

        # Create new segment
        new_segment = Segment.objects.create(session=session, mode=mode, start_at=now, reason=reason)
        
        return Response(SegmentSerializer(new_segment).data, status=status.HTTP_201_CREATED)

class SessionStopView(APIView):
    def post(self, request, pk):
        try:
            session = Session.objects.get(id=pk, user=request.user, status='active')
        except Session.DoesNotExist:
            return Response({"error": "Active session not found"}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        
        # Close open segments
        Segment.objects.filter(session=session, end_at__isnull=True).update(end_at=now)
        
        # End session
        session.status = 'ended'
        session.ended_at = now
        session.save()
        
        return Response(SessionSerializer(session).data)

# History Views
class DailyHistoryView(APIView):
    def get(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({"error": "date param is required (YYYY-MM-DD)"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)

        sessions = Session.objects.filter(
            user=request.user, 
            created_at__date=target_date
        ).prefetch_related('segments', 'todo')
        
        # Group by todo
        # Standard approach: return list of sessions which already have nested segments and todo info.
        # Requirements ask for: "returns sessions + segments grouped by todo with computed durations"
        
        serializer = SessionSerializer(sessions, many=True)
        return Response({
            "date": date_str,
            "timezone": timezone.get_current_timezone_name(),
            "results": serializer.data
        })

class RangeHistoryView(generics.ListAPIView):
    serializer_class = SegmentSerializer

    def get_queryset(self):
        start_str = self.request.query_params.get('start')
        end_str = self.request.query_params.get('end')
        mode = self.request.query_params.get('mode')
        reason = self.request.query_params.get('reason')
        todo_id = self.request.query_params.get('todo_id')

        queryset = Segment.objects.filter(session__user=self.request.user)

        if start_str:
            queryset = queryset.filter(start_at__date__gte=start_str)
        if end_str:
            queryset = queryset.filter(start_at__date__lte=end_str)
        if mode:
            queryset = queryset.filter(mode=mode)
        if reason:
            queryset = queryset.filter(reason=reason)
        if todo_id:
            queryset = queryset.filter(session__todo_id=todo_id)

        return queryset.order_by('-start_at')
