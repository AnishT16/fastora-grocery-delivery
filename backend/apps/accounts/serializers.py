from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, CustomerProfile, Address
from apps.delivery.services.zone_service import get_serviceable_zone
from common.exceptions import ZoneNotServiceableError


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'first_name', 'last_name', 'password', 'password_confirm', 'role']
        extra_kwargs = {
            'role': {'default': User.ROLE_CUSTOMER},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        phone = validated_data.get('phone', '')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Ensure CustomerProfile exists
        CustomerProfile.objects.get_or_create(user=user, defaults={'phone': phone})
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            # Also try email if user supplied email as login
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This user account is inactive.")

        data['user'] = user
        return data


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ['phone', 'avatar', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    profile = CustomerProfileSerializer(read_only=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_active', 'profile']
        read_only_fields = ['id', 'username', 'role', 'is_active']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        phone = validated_data.get('phone', instance.phone)
        instance.phone = phone
        instance.save()

        if hasattr(instance, 'profile') and instance.profile:
            instance.profile.phone = phone
            instance.profile.save()

        return instance


class AddressSerializer(serializers.ModelSerializer):
    delivery_zone_name = serializers.CharField(source='delivery_zone.name', read_only=True)

    class Meta:
        model = Address
        fields = [
            'id',
            'customer',
            'title',
            'street_address',
            'landmark',
            'city',
            'state',
            'postal_code',
            'latitude',
            'longitude',
            'delivery_zone',
            'delivery_zone_name',
            'is_default',
            'created_at',
        ]
        read_only_fields = ['id', 'customer', 'delivery_zone', 'delivery_zone_name', 'created_at']

    def validate(self, attrs):
        # find delivery zone from postal code or coordinates
        postal_code = attrs.get('postal_code') or (self.instance.postal_code if self.instance else None)
        lat = attrs.get('latitude') or (self.instance.latitude if self.instance else None)
        lng = attrs.get('longitude') or (self.instance.longitude if self.instance else None)

        zone = None
        if lat and lng:
            try:
                zone = get_serviceable_zone({'latitude': float(lat), 'longitude': float(lng)})
            except ZoneNotServiceableError:
                pass

        if not zone and postal_code:
            try:
                zone = get_serviceable_zone(str(postal_code))
            except ZoneNotServiceableError:
                pass

        attrs['delivery_zone'] = zone
        return attrs

    def create(self, validated_data):
        customer = self.context['request'].user
        validated_data['customer'] = customer

        # If marked as default, unset other defaults for this customer
        if validated_data.get('is_default', False):
            Address.objects.filter(customer=customer, is_default=True).update(is_default=False)
        elif not Address.objects.filter(customer=customer).exists():
            validated_data['is_default'] = True

        return super().create(validated_data)
