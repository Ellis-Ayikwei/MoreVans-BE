from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import Message
from .serializer import MessageSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Message instances.
    """

    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Support file uploads

    def get_queryset(self):
        user = self.request.user

        # Base queryset - users can only see messages they sent or received
        # unless they're admin
        if user.is_staff or user.is_superuser:
            queryset = Message.objects.all()
        else:
            queryset = Message.objects.filter(Q(sender=user) | Q(receiver=user))

        # Apply query parameter filters
        request_id = self.request.query_params.get("request", None)
        sender_id = self.request.query_params.get("sender", None)
        receiver_id = self.request.query_params.get("receiver", None)
        read = self.request.query_params.get("read", None)
        unread_only = self.request.query_params.get("unread_only", None)

        if request_id:
            queryset = queryset.filter(request_id=request_id)
        if sender_id:
            queryset = queryset.filter(sender_id=sender_id)
        if receiver_id:
            queryset = queryset.filter(receiver_id=receiver_id)
        if read is not None:
            read_bool = read.lower() == "true"
            queryset = queryset.filter(read=read_bool)
        if unread_only and unread_only.lower() == "true":
            queryset = queryset.filter(read=False, receiver=user)

        return queryset.select_related("sender", "receiver", "request").order_by(
            "-created_at"
        )

    def perform_create(self, serializer):
        """Set sender as current user when creating a message"""
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """
        Mark a message as read.
        """
        message = self.get_object()
        if message.receiver != request.user:
            return Response(
                {"detail": "You can only mark messages sent to you as read."},
                status=status.HTTP_403_FORBIDDEN,
            )

        message.read = True
        message.read_at = timezone.now()
        message.save()
        serializer = self.get_serializer(message)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def conversation(self, request):
        """
        Get all messages for a specific request (conversation)
        Usage: /messages/conversation/?request_id=uuid
        """
        request_id = request.query_params.get("request_id")
        if not request_id:
            return Response(
                {"error": "request_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        messages = (
            Message.objects.filter(request_id=request_id)
            .filter(Q(sender=user) | Q(receiver=user))
            .select_related("sender", "receiver")
            .order_by("created_at")
        )

        serializer = MessageSerializer(
            messages, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """
        Get count of unread messages for current user
        Usage: /messages/unread_count/
        """
        user = request.user
        count = Message.objects.filter(receiver=user, read=False).count()
        return Response({"unread_count": count})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """
        Mark all messages as read for current user
        Optional: pass request_id to mark only messages in that conversation
        Usage: POST /messages/mark_all_read/
        Body: {"request_id": "uuid"} (optional)
        """
        user = request.user
        request_id = request.data.get("request_id")

        if request_id:
            # Mark messages in specific conversation as read
            updated = Message.objects.filter(
                request_id=request_id, receiver=user, read=False
            ).update(read=True, read_at=timezone.now())
        else:
            # Mark all user's messages as read
            updated = Message.objects.filter(receiver=user, read=False).update(
                read=True, read_at=timezone.now()
            )

        return Response(
            {"message": f"{updated} messages marked as read", "count": updated}
        )

    @action(detail=False, methods=["get"])
    def my_conversations(self, request):
        """
        Get list of conversations (unique requests) with latest message info
        Usage: /messages/my_conversations/
        """
        user = request.user

        # Get distinct request IDs where user has messages
        conversations = []
        request_ids = (
            Message.objects.filter(Q(sender=user) | Q(receiver=user))
            .values_list("request_id", flat=True)
            .distinct()
        )

        for request_id in request_ids:
            # Get latest message for this request
            latest_message = (
                Message.objects.filter(request_id=request_id)
                .filter(Q(sender=user) | Q(receiver=user))
                .select_related("sender", "receiver", "request")
                .order_by("-created_at")
                .first()
            )

            # Count unread messages in this conversation
            unread_count = Message.objects.filter(
                request_id=request_id, receiver=user, read=False
            ).count()

            if latest_message:
                conversations.append(
                    {
                        "request_id": str(request_id),
                        "request_tracking_number": (
                            latest_message.request.tracking_number
                            if latest_message.request
                            else None
                        ),
                        "latest_message": MessageSerializer(
                            latest_message, context={"request": request}
                        ).data,
                        "unread_count": unread_count,
                        "last_activity": latest_message.created_at,
                    }
                )

        # Sort by last activity
        conversations.sort(key=lambda x: x["last_activity"], reverse=True)

        return Response(conversations)

    @action(detail=False, methods=["post"])
    def send_file(self, request):
        """
        Send a message with file attachment
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def file_types(self, request):
        """
        Get allowed file types and size limits
        """
        return Response(
            {
                "allowed_types": {
                    "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
                    "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf"],
                    "spreadsheets": [".xls", ".xlsx", ".csv"],
                    "presentations": [".ppt", ".pptx"],
                    "archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
                    "other": [".json", ".xml", ".log"],
                },
                "max_file_size": "10MB",
                "max_file_size_bytes": 10 * 1024 * 1024,
            }
        )
