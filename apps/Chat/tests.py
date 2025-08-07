from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Conversation, ConversationParticipant, ChatMessage
from apps.Job.models import Job
from apps.Request.models import Request
from apps.Bidding.models import Bid
from apps.Provider.models import ServiceProvider
import uuid

User = get_user_model()


class ChatModelTests(TestCase):
    """Test chat models"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
    
    def test_create_conversation(self):
        """Test creating a conversation"""
        conversation = Conversation.objects.create(
            title='Test Conversation',
            conversation_type='general'
        )
        self.assertEqual(conversation.title, 'Test Conversation')
        self.assertTrue(conversation.is_active)
        self.assertFalse(conversation.is_archived)
    
    def test_add_participants(self):
        """Test adding participants to conversation"""
        conversation = Conversation.objects.create(
            title='Test Conversation',
            conversation_type='general'
        )
        
        # Add participants
        participant1 = conversation.add_participant(self.user1, role='admin')
        participant2 = conversation.add_participant(self.user2)
        
        self.assertEqual(conversation.participants.count(), 2)
        self.assertEqual(participant1.role, 'admin')
        self.assertEqual(participant2.role, 'participant')
    
    def test_create_message(self):
        """Test creating a message"""
        conversation = Conversation.objects.create(
            title='Test Conversation',
            conversation_type='general'
        )
        conversation.add_participant(self.user1)
        conversation.add_participant(self.user2)
        
        message = ChatMessage.objects.create(
            conversation=conversation,
            sender=self.user1,
            content='Hello, this is a test message',
            message_type='text'
        )
        
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, 'Hello, this is a test message')
        self.assertFalse(message.is_edited)
        self.assertFalse(message.is_deleted)
    
    def test_unread_count(self):
        """Test unread message count"""
        conversation = Conversation.objects.create(
            title='Test Conversation',
            conversation_type='general'
        )
        participant1 = conversation.add_participant(self.user1)
        participant2 = conversation.add_participant(self.user2)
        
        # User1 sends a message
        ChatMessage.objects.create(
            conversation=conversation,
            sender=self.user1,
            content='Test message'
        )
        
        # User2 should have 1 unread message
        self.assertEqual(conversation.get_unread_count(self.user2), 1)
        # User1 should have 0 unread messages
        self.assertEqual(conversation.get_unread_count(self.user1), 0)


class ChatAPITests(APITestCase):
    """Test chat API endpoints"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@test.com',
            password='testpass123'
        )
    
    def test_create_conversation(self):
        """Test creating a conversation via API"""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'title': 'API Test Conversation',
            'conversation_type': 'general',
            'participant_ids': [str(self.user2.id)]
        }
        
        response = self.client.post('/morevans/api/v1/chat/conversations/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'API Test Conversation')
        
        # Check participants
        conversation = Conversation.objects.get(id=response.data['id'])
        self.assertEqual(conversation.participants.count(), 2)
    
    def test_send_message(self):
        """Test sending a message via API"""
        # Create conversation
        conversation = Conversation.objects.create(
            title='Message Test',
            conversation_type='general'
        )
        conversation.add_participant(self.user1)
        conversation.add_participant(self.user2)
        
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'conversation': str(conversation.id),
            'content': 'Test message via API',
            'message_type': 'text'
        }
        
        response = self.client.post('/morevans/api/v1/chat/messages/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test message via API')
        self.assertEqual(response.data['sender']['id'], str(self.user1.id))
    
    def test_list_conversations(self):
        """Test listing user's conversations"""
        # Create conversations
        conv1 = Conversation.objects.create(title='Conv 1', conversation_type='general')
        conv1.add_participant(self.user1)
        conv1.add_participant(self.user2)
        
        conv2 = Conversation.objects.create(title='Conv 2', conversation_type='general')
        conv2.add_participant(self.user1)
        conv2.add_participant(self.user3)
        
        conv3 = Conversation.objects.create(title='Conv 3', conversation_type='general')
        conv3.add_participant(self.user2)
        conv3.add_participant(self.user3)
        
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/morevans/api/v1/chat/conversations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # User1 is in 2 conversations
    
    def test_conversation_permissions(self):
        """Test that users can only see conversations they're part of"""
        conversation = Conversation.objects.create(
            title='Private Conv',
            conversation_type='general'
        )
        conversation.add_participant(self.user1)
        conversation.add_participant(self.user2)
        
        # User3 shouldn't be able to access this conversation
        self.client.force_authenticate(user=self.user3)
        
        response = self.client.get(f'/morevans/api/v1/chat/conversations/{conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_mark_messages_read(self):
        """Test marking messages as read"""
        conversation = Conversation.objects.create(
            title='Read Test',
            conversation_type='general'
        )
        conversation.add_participant(self.user1)
        conversation.add_participant(self.user2)
        
        # User1 sends messages
        msg1 = ChatMessage.objects.create(
            conversation=conversation,
            sender=self.user1,
            content='Message 1'
        )
        msg2 = ChatMessage.objects.create(
            conversation=conversation,
            sender=self.user1,
            content='Message 2'
        )
        
        self.client.force_authenticate(user=self.user2)
        
        # Mark messages as read
        data = {'message_ids': [str(msg1.id), str(msg2.id)]}
        response = self.client.post('/morevans/api/v1/chat/messages/mark_multiple_read/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        
        # Check unread count is now 0
        self.assertEqual(conversation.get_unread_count(self.user2), 0)
    
    def test_support_conversation(self):
        """Test creating a support conversation"""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'support_type': 'technical',
            'title': 'Need help with my account',
            'message': 'I cannot log in to my account'
        }
        
        response = self.client.post('/morevans/api/v1/chat/conversations/create_support_conversation/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['conversation_type'], 'support')
        
        # Check that initial message was created
        conversation = Conversation.objects.get(id=response.data['id'])
        messages = conversation.messages.all()
        self.assertEqual(messages.count(), 2)  # User message + system message