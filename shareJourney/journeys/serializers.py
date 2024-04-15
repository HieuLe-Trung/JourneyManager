from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import User, Journey


class UserSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['avatar'] = instance.avatar.url
        return rep

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'phone', 'password', 'email',
                  'avatar']  # những trường user POST lên khi đăng ký
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {
                'write_only': 'True'
            }
        }

    def create(self, validated_data):
        data = validated_data.copy()

        user = User(**data)
        user.set_password((data['password']))
        user.save()
        return user


class JourneySerializer(serializers.ModelSerializer):
    user_create = UserSerializer(read_only=True)

    class Meta:
        model = Journey
        fields = ['user_create', 'name_journey', 'start_location', 'end_location', 'departure_time', 'distance',
                  'estimated_time']
        read_only_fields = ['distance', 'estimated_time']
