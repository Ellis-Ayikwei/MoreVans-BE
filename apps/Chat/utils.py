from django.contrib.contenttypes.models import ContentType
from .models import Conversation, ConversationParticipant


def create_conversation_for_object(obj, conversation_type, title=None, participants=None, creator=None):
    """
    Create a conversation linked to any model object
    
    Args:
        obj: The model instance to link the conversation to
        conversation_type: Type of conversation ('job', 'bid', 'request', etc.)
        title: Optional title for the conversation
        participants: List of User objects to add as participants
        creator: User who is creating the conversation (will be admin)
    
    Returns:
        Conversation instance
    """
    content_type = ContentType.objects.get_for_model(obj)
    
    conversation = Conversation.objects.create(
        title=title or f"{conversation_type.title()} Discussion - {str(obj)}",
        conversation_type=conversation_type,
        content_type=content_type,
        object_id=obj.id
    )
    
    # Add creator as admin if provided
    if creator:
        conversation.add_participant(creator, role='admin')
    
    # Add other participants
    if participants:
        for user in participants:
            if user != creator:  # Don't add creator twice
                conversation.add_participant(user)
    
    return conversation


def get_or_create_conversation_for_object(obj, conversation_type, **kwargs):
    """
    Get existing conversation or create new one for an object
    
    Args:
        obj: The model instance
        conversation_type: Type of conversation
        **kwargs: Additional arguments for create_conversation_for_object
    
    Returns:
        tuple: (conversation, created)
    """
    content_type = ContentType.objects.get_for_model(obj)
    
    conversation = Conversation.objects.filter(
        content_type=content_type,
        object_id=obj.id,
        conversation_type=conversation_type
    ).first()
    
    if conversation:
        return conversation, False
    
    conversation = create_conversation_for_object(
        obj, conversation_type, **kwargs
    )
    return conversation, True


def create_bid_conversation(bid):
    """
    Create a conversation for a bid negotiation
    
    Args:
        bid: Bid instance
    
    Returns:
        Conversation instance
    """
    participants = []
    
    # Add provider
    if hasattr(bid, 'provider') and bid.provider:
        if hasattr(bid.provider, 'user'):
            participants.append(bid.provider.user)
    
    # Add job requester
    if hasattr(bid, 'job') and bid.job:
        if hasattr(bid.job, 'request') and bid.job.request:
            if hasattr(bid.job.request, 'user'):
                participants.append(bid.job.request.user)
    
    title = f"Bid Discussion - {bid.job.title if bid.job else 'Unknown Job'}"
    
    return create_conversation_for_object(
        bid,
        'bid',
        title=title,
        participants=participants,
        creator=participants[0] if participants else None
    )


def create_job_conversation(job):
    """
    Create a conversation for a job
    
    Args:
        job: Job instance
    
    Returns:
        Conversation instance
    """
    participants = []
    
    # Add job requester
    if hasattr(job, 'request') and job.request:
        if hasattr(job.request, 'user'):
            participants.append(job.request.user)
    
    # Add assigned provider if any
    if hasattr(job, 'assigned_provider') and job.assigned_provider:
        if hasattr(job.assigned_provider, 'user'):
            participants.append(job.assigned_provider.user)
    
    title = f"Job Discussion - {job.title or job.job_number}"
    
    return create_conversation_for_object(
        job,
        'job',
        title=title,
        participants=participants,
        creator=participants[0] if participants else None
    )


def create_request_conversation(request_obj):
    """
    Create a conversation for a request
    
    Args:
        request_obj: Request instance
    
    Returns:
        Conversation instance
    """
    participants = []
    
    # Add request creator
    if hasattr(request_obj, 'user'):
        participants.append(request_obj.user)
    
    title = f"Request Discussion - {request_obj.tracking_number}"
    
    return create_conversation_for_object(
        request_obj,
        'request',
        title=title,
        participants=participants,
        creator=participants[0] if participants else None
    )


def create_support_conversation(user, support_type='general', title=None):
    """
    Create a support conversation
    
    Args:
        user: User requesting support
        support_type: Type of support ('general', 'technical', 'billing', etc.)
        title: Optional title for the conversation
    
    Returns:
        Conversation instance
    """
    from apps.User.models import User
    
    # Get support staff (you might want to customize this logic)
    support_staff = User.objects.filter(
        is_staff=True,
        is_active=True
    ).first()
    
    participants = [user]
    if support_staff and support_staff != user:
        participants.append(support_staff)
    
    conversation = Conversation.objects.create(
        title=title or f"Support Request - {support_type.title()}",
        conversation_type='support',
        metadata={'support_type': support_type}
    )
    
    # Add user as participant
    conversation.add_participant(user, role='participant')
    
    # Add support staff as moderator
    if support_staff and support_staff != user:
        conversation.add_participant(support_staff, role='moderator')
    
    return conversation


def create_dispute_conversation(dispute):
    """
    Create a conversation for a dispute
    
    Args:
        dispute: Dispute instance
    
    Returns:
        Conversation instance
    """
    participants = []
    
    # Add dispute raiser
    if hasattr(dispute, 'raised_by'):
        participants.append(dispute.raised_by)
    
    # Add other party from the request
    if hasattr(dispute, 'request') and dispute.request:
        if hasattr(dispute.request, 'user') and dispute.request.user != dispute.raised_by:
            participants.append(dispute.request.user)
        
        # Add provider if assigned
        if hasattr(dispute.request, 'job') and dispute.request.job:
            if hasattr(dispute.request.job, 'assigned_provider') and dispute.request.job.assigned_provider:
                if hasattr(dispute.request.job.assigned_provider, 'user'):
                    provider_user = dispute.request.job.assigned_provider.user
                    if provider_user not in participants:
                        participants.append(provider_user)
    
    title = f"Dispute Resolution - {dispute.dispute_type.title()}"
    
    return create_conversation_for_object(
        dispute,
        'dispute',
        title=title,
        participants=participants,
        creator=dispute.raised_by if hasattr(dispute, 'raised_by') else None
    )


def add_system_message(conversation, content, metadata=None):
    """
    Add a system message to a conversation
    
    Args:
        conversation: Conversation instance
        content: Message content
        metadata: Optional metadata dict
    
    Returns:
        ChatMessage instance
    """
    from .models import ChatMessage
    
    return ChatMessage.objects.create(
        conversation=conversation,
        sender=None,  # System message
        content=content,
        message_type='system',
        metadata=metadata or {}
    )