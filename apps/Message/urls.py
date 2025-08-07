from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'chat-rooms', views.ChatRoomViewSet, basename='chatroom')
router.register(r'chat-messages', views.ChatMessageViewSet, basename='chatmessage')
router.register(r'messages', views.MessageViewSet, basename='message')

app_name = "Message"

urlpatterns = [
    # Include router URLs for ViewSets
    path('api/v1/', include(router.urls)),
    
    # Chat system status and utilities
    path('api/v1/chat/status/', views.ChatSystemStatusView.as_view(), name='chat-status'),
    
    # Original Message API endpoints (for backward compatibility)
    path('api/v1/messages/list/', views.MessageListView.as_view(), name='message-list'),
    path('api/v1/messages/create/', views.MessageCreateView.as_view(), name='message-create'),
    path('api/v1/messages/<uuid:pk>/', views.MessageDetailView.as_view(), name='message-detail'),
    path('api/v1/messages/<uuid:pk>/mark-read/', views.MessageMarkReadView.as_view(), name='message-mark-read'),
    path('api/v1/conversations/<uuid:user_id>/', views.ConversationView.as_view(), name='conversation'),
    path('api/v1/conversations/', views.GetConversationsView.as_view(), name='conversations-list'),
]
