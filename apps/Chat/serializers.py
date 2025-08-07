from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import (
    Conversation, ConversationParticipant, 
    ChatMessage, MessageReaction, MessageRead
)
from apps.User.serializer import UserSerializer


class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'emoji', 'created_at']
        read_only_fields = ['created_at']


class MessageReadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageRead
        fields = ['id', 'user', 'read_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    read_receipts = MessageReadSerializer(many=True, read_only=True)
    reply_to_data = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()
    formatted_file_size = serializers.CharField(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'conversation', 'sender', 'content', 'message_type',
            'attachment', 'attachment_url', 'attachment_name', 
            'attachment_size', 'formatted_file_size', 'attachment_type',
            'metadata', 'is_edited', 'edited_at', 'is_deleted', 
            'deleted_at', 'reply_to', 'reply_to_data', 'reactions',
            'read_receipts', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'sender', 'attachment_url', 'formatted_file_size',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'attachment': {'write_only': True}
        }
    
    def get_reply_to_data(self, obj):
        if obj.reply_to:
            return {
                'id': str(obj.reply_to.id),
                'sender': obj.reply_to.sender.username if obj.reply_to.sender else 'System',
                'content': obj.reply_to.content[:100],
                'message_type': obj.reply_to.message_type
            }
        return None
    
    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None


class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ConversationParticipant
        fields = [
            'id', 'user', 'role', 'is_active', 'last_read_at',
            'joined_at', 'left_at', 'notify_on_message', 
            'notify_on_mention', 'unread_count'
        ]
        read_only_fields = ['joined_at', 'left_at', 'unread_count']
    
    def get_unread_count(self, obj):
        return obj.conversation.get_unread_count(obj.user)


class ConversationSerializer(serializers.ModelSerializer):
    participants = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    content_object_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'conversation_type', 'content_type',
            'object_id', 'content_object_data', 'is_active',
            'is_archived', 'allow_attachments', 'max_attachment_size',
            'participants', 'last_message', 'unread_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_last_message(self, obj):
        last_msg = obj.messages.filter(is_deleted=False).last()
        if last_msg:
            return ChatMessageSerializer(last_msg, context=self.context).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0
    
    def get_content_object_data(self, obj):
        if obj.content_object:
            # Return basic info about the linked object
            return {
                'type': obj.content_type.model,
                'id': str(obj.object_id),
                'display': str(obj.content_object)
            }
        return None


class ConversationCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    content_type_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Conversation
        fields = [
            'title', 'conversation_type', 'content_type_name',
            'object_id', 'allow_attachments', 'max_attachment_size',
            'participant_ids'
        ]
    
    def validate(self, attrs):
        # Convert content_type_name to content_type
        content_type_name = attrs.pop('content_type_name', None)
        if content_type_name:
            try:
                app_label, model = content_type_name.split('.')
                content_type = ContentType.objects.get(
                    app_label=app_label, 
                    model=model
                )
                attrs['content_type'] = content_type
            except (ValueError, ContentType.DoesNotExist):
                raise serializers.ValidationError(
                    f"Invalid content_type_name: {content_type_name}"
                )
        
        return attrs
    
    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = super().create(validated_data)
        
        # Add creator as admin
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            conversation.add_participant(request.user, role='admin')
        
        # Add other participants
        from apps.User.models import User
        for user_id in participant_ids:
            try:
                user = User.objects.get(id=user_id)
                conversation.add_participant(user)
            except User.DoesNotExist:
                pass
        
        return conversation


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'conversation', 'content', 'message_type',
            'attachment', 'metadata', 'reply_to'
        ]
    
    def validate_conversation(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if user is a participant
            if not value.participants.filter(
                user=request.user, 
                is_active=True
            ).exists():
                raise serializers.ValidationError(
                    "You are not a participant in this conversation"
                )
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['sender'] = request.user
        return super().create(validated_data)