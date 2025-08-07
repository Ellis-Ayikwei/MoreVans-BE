from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from .models import Message, ChatRoom, ChatMessage, ChatMessageRead
from apps.User.models import User
from apps.Request.models import Request


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    receiver_username = serializers.CharField(source="receiver.username", read_only=True)
    request_title = serializers.CharField(source="request.title", read_only=True)
    formatted_file_size = serializers.CharField(read_only=True)
    attachment_url = serializers.CharField(read_only=True)
    file_extension = serializers.CharField(read_only=True)
    time_since_created = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "request",
            "sender",
            "receiver",
            "content",
            "attachment",
            "attachment_name",
            "attachment_size",
            "attachment_type",
            "attachment_url",
            "formatted_file_size",
            "file_extension",
            "message_type",
            "read",
            "read_at",
            "created_at",
            "updated_at",
            "sender_username",
            "receiver_username",
            "request_title",
            "time_since_created",
        ]
        read_only_fields = [
            "id",
            "attachment_name",
            "attachment_size",
            "attachment_type",
            "message_type",
            "created_at",
            "updated_at",
            "sender_username",
            "receiver_username",
            "request_title",
            "formatted_file_size",
            "attachment_url",
            "file_extension",
            "time_since_created",
        ]

    def get_time_since_created(self, obj):
        """Get human-readable time since creation"""
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        diff = now - obj.created_at

        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        else:
            return obj.created_at.strftime("%Y-%m-%d %H:%M")

    def validate(self, data):
        """Validate that content or attachment is provided"""
        if not data.get("content", "").strip() and not data.get("attachment"):
            raise serializers.ValidationError(
                "Either content or attachment must be provided."
            )
        return data


class ChatRoomSerializer(serializers.ModelSerializer):
    participants_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    related_object_data = serializers.SerializerMethodField()
    participants_data = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'name',
            'room_type',
            'content_type',
            'object_id',
            'participants',
            'is_active',
            'is_private',
            'last_message_at',
            'created_at',
            'updated_at',
            'participants_count',
            'last_message',
            'unread_count',
            'related_object_data',
            'participants_data',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'participants_count',
            'last_message',
            'unread_count',
            'related_object_data',
            'participants_data',
        ]

    def get_participants_count(self, obj):
        return obj.participants.count()

    def get_last_message(self, obj):
        last_message = obj.get_last_message()
        if last_message:
            return {
                'id': last_message.id,
                'content': last_message.content,
                'sender': last_message.sender.username,
                'message_type': last_message.message_type,
                'created_at': last_message.created_at,
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.chat_messages.exclude(
                read_by=request.user
            ).exclude(sender=request.user).count()
        return 0

    def get_related_object_data(self, obj):
        """Get data about the related object (Request, Job, Bid, etc.)"""
        if obj.related_object:
            if hasattr(obj.related_object, 'title'):
                return {
                    'type': obj.content_type.model,
                    'id': obj.object_id,
                    'title': obj.related_object.title,
                }
            elif hasattr(obj.related_object, 'job_number'):
                return {
                    'type': obj.content_type.model,
                    'id': obj.object_id,
                    'job_number': obj.related_object.job_number,
                }
            elif hasattr(obj.related_object, 'amount'):
                return {
                    'type': obj.content_type.model,
                    'id': obj.object_id,
                    'amount': str(obj.related_object.amount),
                }
        return None

    def get_participants_data(self, obj):
        """Get basic data about participants"""
        return [
            {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
            for user in obj.participants.all()
        ]


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    related_model = serializers.CharField(write_only=True, required=False)
    related_id = serializers.IntegerField(write_only=True, required=False)
    participants_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ChatRoom
        fields = [
            'name',
            'room_type',
            'is_private',
            'related_model',
            'related_id',
            'participants_ids',
        ]

    def validate(self, data):
        """Validate related model and participants"""
        related_model = data.get('related_model')
        related_id = data.get('related_id')

        if related_model and related_id:
            # Import models here to avoid circular import
            from apps.Job.models import Job
            from apps.Bidding.models import Bid
            
            # Validate that the related model exists
            valid_models = {
                'request': Request,
                'job': Job,
                'bid': Bid,
            }
            
            if related_model not in valid_models:
                raise serializers.ValidationError(
                    f"Invalid related_model. Must be one of: {list(valid_models.keys())}"
                )
            
            model_class = valid_models[related_model]
            try:
                related_object = model_class.objects.get(id=related_id)
                data['related_object'] = related_object
            except model_class.DoesNotExist:
                raise serializers.ValidationError(
                    f"{related_model.title()} with id {related_id} does not exist"
                )

        return data

    def create(self, validated_data):
        participants_ids = validated_data.pop('participants_ids', [])
        related_model = validated_data.pop('related_model', None)
        related_id = validated_data.pop('related_id', None)
        related_object = validated_data.pop('related_object', None)

        # Set content type and object id if related object exists
        if related_object:
            validated_data['content_type'] = ContentType.objects.get_for_model(related_object)
            validated_data['object_id'] = related_object.id

        chat_room = ChatRoom.objects.create(**validated_data)

        # Add participants
        if participants_ids:
            users = User.objects.filter(id__in=participants_ids)
            chat_room.participants.set(users)

        # Add current user as participant if authenticated
        request = self.context.get('request')
        if request and request.user:
            chat_room.add_participant(request.user)

        return chat_room


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_data = serializers.SerializerMethodField()
    attachment_url = serializers.CharField(read_only=True)
    formatted_file_size = serializers.CharField(read_only=True)
    time_since_created = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    reply_to_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'chat_room',
            'sender',
            'content',
            'message_type',
            'attachment',
            'attachment_name',
            'attachment_size',
            'attachment_type',
            'attachment_url',
            'formatted_file_size',
            'reply_to',
            'system_data',
            'created_at',
            'updated_at',
            'sender_data',
            'time_since_created',
            'is_read',
            'reply_to_message',
        ]
        read_only_fields = [
            'id',
            'attachment_name',
            'attachment_size',
            'attachment_type',
            'created_at',
            'updated_at',
            'sender_data',
            'attachment_url',
            'formatted_file_size',
            'time_since_created',
            'is_read',
            'reply_to_message',
        ]

    def get_sender_data(self, obj):
        return {
            'id': obj.sender.id,
            'username': obj.sender.username,
            'first_name': obj.sender.first_name,
            'last_name': obj.sender.last_name,
        }

    def get_time_since_created(self, obj):
        """Get human-readable time since creation"""
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        diff = now - obj.created_at

        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        else:
            return obj.created_at.strftime("%Y-%m-%d %H:%M")

    def get_is_read(self, obj):
        """Check if current user has read this message"""
        request = self.context.get('request')
        if request and request.user:
            return obj.read_by.filter(id=request.user.id).exists()
        return False

    def get_reply_to_message(self, obj):
        """Get basic info about the message being replied to"""
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'content': obj.reply_to.content[:100] + ('...' if len(obj.reply_to.content) > 100 else ''),
                'sender': obj.reply_to.sender.username,
                'message_type': obj.reply_to.message_type,
            }
        return None

    def validate(self, data):
        """Validate message content and chat room access"""
        chat_room = data.get('chat_room')
        request = self.context.get('request')
        
        # Check if user is participant in the chat room
        if chat_room and request and request.user:
            if not chat_room.participants.filter(id=request.user.id).exists():
                raise serializers.ValidationError(
                    "You are not a participant in this chat room."
                )
        
        # Validate that content or attachment is provided for non-system messages
        message_type = data.get('message_type', 'text')
        if message_type not in ['system', 'bid_update', 'status_update']:
            if not data.get('content', '').strip() and not data.get('attachment'):
                raise serializers.ValidationError(
                    "Either content or attachment must be provided."
                )
        
        return data

    def create(self, validated_data):
        # Set sender to current user
        request = self.context.get('request')
        if request and request.user:
            validated_data['sender'] = request.user
        
        return super().create(validated_data)


class ChatMessageReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessageRead
        fields = ['message', 'user', 'read_at']
        read_only_fields = ['read_at']


class BulkMarkAsReadSerializer(serializers.Serializer):
    message_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    
    def validate_message_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one message ID is required.")
        return value
