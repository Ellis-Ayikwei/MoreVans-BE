from apps.User.models import User, Address, UserActivity
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone_number', 
                 'profile_picture', 'rating', 'user_type', 'account_status', 
                 'last_active', 'date_joined')
        read_only_fields = ('rating', 'last_active', 'date_joined')

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address_user', 'address_line1', 'address_line2', 
                 'city', 'state', 'postal_code', 'country', 'address_type']

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'activity_type', 'request', 'timestamp', 'details']
        read_only_fields = ['timestamp']

