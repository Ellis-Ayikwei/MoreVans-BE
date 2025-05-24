from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
import logging

from .models import User, Address, UserActivity
from .serializer import UserSerializer, AddressSerializer, UserActivitySerializer
from apps.Request.models import Request

logger = logging.getLogger(__name__)

class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.user_type in ['admin']

class IsSuperAdminUser(permissions.BasePermission):
    """
    Permission to only allow super admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

class IsProviderUser(permissions.BasePermission):
    """
    Permission to only allow provider users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.user_type == 'provider'

class IsCustomerUser(permissions.BasePermission):
    """
    Permission to only allow customer users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.user_type == 'customer'

class IsSelfOrAdmin(permissions.BasePermission):
    """
    Allow users to edit their own profiles, and admins to edit any profile.
    """
    def has_object_permission(self, request, view, obj):
        # Allow admins to edit any user
        if request.user.user_type in ['admin'] or request.user.is_superuser:
            return True
        
        # Allow users to edit themselves
        return obj.id == request.user.id

class UserManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing all types of users.
    Provides CRUD operations and additional actions for user management.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    
    def get_permissions(self):
        """
        Custom permissions based on action:
        - List/retrieve: Any authenticated user
        - Create: Admin users only (except for create_customer action)
        - Update/delete: Admin or self
        """
        if self.action == 'create':
            permission_classes = [IsAdminUser | IsSuperAdminUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsSelfOrAdmin]
        elif self.action in ['create_customer', 'create_provider', 'create_admin']:
            if self.action == 'create_customer':
                permission_classes = [permissions.AllowAny]
            else:
                permission_classes = [IsAdminUser | IsSuperAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
            
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Customizes the queryset based on user type and query parameters.
        - Admins can see all users
        - Regular users can only see themselves
        """
        queryset = User.objects.all()
        
        # Filter by user type if specified
        user_type = self.request.query_params.get('type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
            
        # Filter by status if specified
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(account_status=status_param)
            
        # Search by name or email if specified
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | 
                Q(first_name__icontains=search) | 
                Q(last_name__icontains=search) |
                Q(phone_number__icontains=search)
            )
            
        # Regular users can only see themselves, admins can see all
        if not (self.request.user.user_type in ['admin'] or self.request.user.is_superuser):
            queryset = queryset.filter(id=self.request.user.id)
            
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def create_customer(self, request):
        """
        Creates a new customer user.
        This endpoint is publicly accessible to allow customer registration.
        """
        data = request.data.copy()
        data['user_type'] = 'customer'
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            # Hash the password
            if 'password' in data:
                serializer.validated_data['password'] = make_password(data['password'])
            
            user = serializer.save()
            return Response(
                self.get_serializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser | IsSuperAdminUser])
    def create_provider(self, request):
        """
        Creates a new service provider user.
        Only accessible to admin users.
        """
        data = request.data.copy()
        data['user_type'] = 'provider'
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            # Hash the password
            if 'password' in data:
                serializer.validated_data['password'] = make_password(data['password'])
            
            user = serializer.save()
            logger.info(f"Provider user created by admin {request.user.id}: {user.id}")
            return Response(
                self.get_serializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsSuperAdminUser])
    def create_admin(self, request):
        """
        Creates a new admin user.
        Only accessible to super admin users.
        """
        data = request.data.copy()
        data['user_type'] = 'admin'
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            # Hash the password
            if 'password' in data:
                serializer.validated_data['password'] = make_password(data['password'])
            
            user = serializer.save()
            logger.info(f"Admin user created by super admin {request.user.id}: {user.id}")
            return Response(
                self.get_serializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser | IsSuperAdminUser])
    def activate(self, request, pk=None):
        """
        Activates a user account.
        Only accessible to admin users.
        """
        user = self.get_object()
        user.account_status = 'active'
        user.save()
        
        logger.info(f"User {user.id} activated by admin {request.user.id}")
        return Response({"status": "User activated successfully"})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser | IsSuperAdminUser])
    def deactivate(self, request, pk=None):
        """
        Deactivates a user account.
        Only accessible to admin users.
        """
        user = self.get_object()
        user.account_status = 'inactive'
        user.save()
        
        logger.info(f"User {user.id} deactivated by admin {request.user.id}")
        return Response({"status": "User deactivated successfully"})
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdminUser])
    def promote_to_admin(self, request, pk=None):
        """
        Promotes a user to admin role.
        Only accessible to super admin users.
        """
        user = self.get_object()
        user.user_type = 'admin'
        user.save()
        
        logger.info(f"User {user.id} promoted to admin by super admin {request.user.id}")
        return Response({"status": "User promoted to admin successfully"})
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Returns the current user's profile.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """
        Returns a user's activity history.
        Regular users can only see their own activity.
        """
        user = self.get_object()
        activities = UserActivity.objects.filter(user=user).order_by('-timestamp')
        
        page = self.paginate_queryset(activities)
        if page is not None:
            serializer = UserActivitySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def requests(self, request, pk=None):
        """
        Returns a user's requests.
        Filtered by status if specified.
        """
        user = self.get_object()
        
        # Check if user is requesting their own data or is an admin
        if user.id != request.user.id and not (request.user.user_type in ['admin'] or request.user.is_superuser):
            return Response(
                {"detail": "You do not have permission to view this user's requests."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        status_filter = request.query_params.get('status')
        requests = Request.objects.filter(user=user)
        
        if status_filter:
            requests = requests.filter(status=status_filter)
            
        from Request.serializer import RequestSerializer
        serializer = RequestSerializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser | IsSuperAdminUser])
    def stats(self, request):
        """
        Returns user statistics.
        Only accessible to admin users.
        """
        total_users = User.objects.count()
        total_customers = User.objects.filter(user_type='customer').count()
        total_providers = User.objects.filter(user_type='provider').count()
        total_admins = User.objects.filter(user_type='admin').count()
        
        active_users = User.objects.filter(account_status='active').count()
        inactive_users = User.objects.filter(account_status='inactive').count()
        
        # New users in the last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
        
        # Request statistics by user type
        customer_requests = Request.objects.filter(user__user_type='customer').count()
        
        stats = {
            'total_users': total_users,
            'by_type': {
                'customers': total_customers,
                'providers': total_providers,
                'admins': total_admins,
            },
            'by_status': {
                'active': active_users,
                'inactive': inactive_users,
            },
            'new_users_30d': new_users_30d,
            'requests': {
                'total_customer_requests': customer_requests,
            }
        }
        
        return Response(stats)

class AddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user addresses.
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Regular users can only see their own addresses.
        Admins can see all addresses.
        """
        queryset = Address.objects.all()
        
        # Regular users can only see their own addresses
        if not (self.request.user.user_type in ['admin'] or self.request.user.is_superuser):
            queryset = queryset.filter(address_user=self.request.user)
            
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create a new address for a user.
        Regular users can only create addresses for themselves.
        """
        # If user_id not specified, use the current user
        if 'address_user' not in request.data:
            request.data['address_user'] = request.user.id
        
        # Regular users can only create addresses for themselves
        if not (request.user.user_type in ['admin'] or request.user.is_superuser):
            if str(request.data.get('address_user')) != str(request.user.id):
                return Response(
                    {"detail": "You can only create addresses for yourself."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_addresses(self, request):
        """
        Returns the current user's addresses.
        """
        addresses = Address.objects.filter(address_user=request.user)
        serializer = self.get_serializer(addresses, many=True)
        return Response(serializer.data)

class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user activity.
    Users can only see their own activity.
    Admins can see all activity.
    """
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        """
        queryset = UserActivity.objects.all()
        
        # Regular users can only see their own activity
        if not (self.request.user.user_type in ['admin'] or self.request.user.is_superuser):
            queryset = queryset.filter(user=self.request.user)
            
        return queryset.order_by('-timestamp')