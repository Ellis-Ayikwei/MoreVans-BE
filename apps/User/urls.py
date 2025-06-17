from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserManagementViewSet,
    AddressViewSet,
    UserActivityViewSet,
    GroupManagementViewSet,
    PermissionManagementViewSet,
    UserGroupManagementViewSet,
)

router = DefaultRouter(trailing_slash=True)
router.register(r"users", UserManagementViewSet, basename="users")
router.register(r"addresses", AddressViewSet, basename="addresses")
router.register(r"activities", UserActivityViewSet, basename="activities")
router.register(r"groups", GroupManagementViewSet, basename="groups")
router.register(r"permissions", PermissionManagementViewSet, basename="permissions")
router.register(r"user-groups", UserGroupManagementViewSet, basename="user-groups")

urlpatterns = [
    path("", include(router.urls)),
]


# Your API endpoints will be:
# GET/POST /api/users/ - List/create users
# GET/PUT/PATCH/DELETE /api/users/{id}/ - User CRUD
# POST /api/users/create_customer/ - Create customer
# POST /api/users/create_provider/ - Create provider
# POST /api/users/create_admin/ - Create admin
# POST /api/users/{id}/activate/ - Activate user
# POST /api/users/{id}/deactivate/ - Deactivate user
# POST /api/users/{id}/update_groups/ - Update user groups
# POST /api/users/{id}/add_to_groups/ - Add user to groups
# POST /api/users/{id}/remove_from_groups/ - Remove user from groups
# POST /api/users/{id}/update_permissions/ - Update user permissions
# GET /api/users/{id}/groups_and_permissions/ - Get user groups/permissions
# GET /api/users/stats/ - Basic user stats
# GET /api/users/advanced_stats/ - Enhanced stats with groups
# GET /api/users/me/ - Current user profile

# GET/POST /api/groups/ - List/create groups
# GET/PUT/PATCH/DELETE /api/groups/{id}/ - Group CRUD
# POST /api/groups/{id}/add_users/ - Add users to group
# POST /api/groups/{id}/remove_users/ - Remove users from group
# POST /api/groups/{id}/update_permissions/ - Update group permissions
# GET /api/groups/{id}/available_users/ - Get users not in group

# GET /api/permissions/ - List all permissions
# GET /api/permissions/by_content_type/ - Permissions grouped by content type

# POST /api/user-groups/bulk_add_to_groups/ - Bulk add users to groups
# POST /api/user-groups/bulk_remove_from_groups/ - Bulk remove users from groups
# POST /api/user-groups/assign_user_to_groups/ - Assign user to groups (replace)
# GET /api/user-groups/users_with_groups/ - All users with group info
