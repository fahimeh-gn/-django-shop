from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Profile
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.db import transaction

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["phone", "address", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['username', 'email']

    def update(self, instance, validated_data):

        profile_data = validated_data.pop('profile', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()


        if profile_data:

            Profile.objects.update_or_create(
                user=instance,
                defaults=profile_data
            )

        return instance





class RegisterSerializer(serializers.ModelSerializer):
 
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="This username is already taken.")]
    )

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],  
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user



class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"]
        )
        if not user:
            raise serializers.ValidationError("Invalid username or password")
        attrs["user"] = user
        return attrs
