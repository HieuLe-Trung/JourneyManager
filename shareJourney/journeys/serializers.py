from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password', 'email',
                  'avatar']  # những trường user POST lên khi đăng ký
        extra_kwargs = {
            'password': {
                'write_only': 'True'
            }
        }

    def create(self, validated_data):
        data = validated_data.copy()

        user = User(**data)
        user.set_password((data['password']))  # băm
        user.save()
        return user
