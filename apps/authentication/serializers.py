from rest_framework import serializers
from .models import User, UserRole, AppRole

class UserRoleSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'role', 'role_display', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    roles = UserRoleSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 
            'full_name', 'phone', 'avatar', 'establishment', 
            'establishment_name', 'roles', 'is_staff', 'is_active'
        ]
        read_only_fields = ['id', 'is_staff', 'is_active']

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
