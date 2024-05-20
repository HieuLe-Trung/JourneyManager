from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import User, Journey, Image, Post, Comment, Notification, CommentJourney, Participation


class UserSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['avatar'] = instance.avatar.url
        return rep

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'phone', 'email', 'password',
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

    def patch(self, instance, validated_data):
        email = validated_data.get('email', instance.email)
        phone = validated_data.get('phone', instance.phone)

        # Kiểm tra xem email hoặc phone đã tồn tại trong cơ sở dữ liệu hay không
        if User.objects.exclude(id=instance.id).filter(email=email).exists():
            raise ValidationError("Email đã tồn tại trong hệ thống.")
        if User.objects.exclude(id=instance.id).filter(phone=phone).exists():
            raise ValidationError("Số điện thoại đã tồn tại trong hệ thống.")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class JourneySerializer(serializers.ModelSerializer):
    user_create = UserSerializer(read_only=True)

    class Meta:
        model = Journey
        fields = ['user_create', 'id', 'name_journey', 'background', 'start_location', 'end_location', 'departure_time']


class JourneyDetailSerializers(JourneySerializer):
    liked = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    def get_liked(self, journey):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return journey.likejourney_set.filter(active=True).exists()

    def get_likes_count(self, journey):
        return journey.likejourney_set.filter(active=True).count()  # lấy những like của hành trình đó active=true

    def get_comments_count(self, journey):
        return CommentJourney.objects.filter(journey=journey).count()

    class Meta:
        model = JourneySerializer.Meta.model
        fields = JourneySerializer.Meta.fields + ['distance', 'estimated_time', 'liked', 'likes_count', 'active',
                                                  'lock_cmt', 'comments_count']


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'image']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['image'] = instance.image.url
        return rep


class PostSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, required=False)
    user = UserSerializer(read_only=True)
    journey = JourneySerializer

    class Meta:
        model = Post
        fields = ['id', 'journey', 'user', 'content', 'visit_point', 'estimated_time_of_arrival', 'created_date',
                  'images']
        read_only_fields = ['created_date']

    def create(self, validated_data):
        images_data = self.context.get('request').FILES.getlist('images')
        post = Post.objects.create(**validated_data)
        for image_data in images_data:
            Image.objects.create(post=post, image=image_data)
        return post


class PostDetailSerializer(PostSerializer):
    liked = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    def get_liked(self, post):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return post.likepost_set.filter(user=request.user, active=True).exists()

    def get_likes_count(self, journey):
        return journey.likepost_set.filter(active=True).count()

    def get_comments_count(self, post):
        return Comment.objects.filter(post=post).count()

    class Meta:
        model = PostSerializer.Meta.model
        fields = PostSerializer.Meta.fields + ['liked', 'likes_count', 'comments_count']


class CommentSerializers(serializers.ModelSerializer):  # update ko dùng detail, nó yêu cầu user
    class Meta:
        model = Comment
        fields = ['id', 'content']


class CommentDetailSerializers(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Comment
        fields = ['user', 'id', 'content', 'created_date']


class CommentJourneySerializers(serializers.ModelSerializer):
    class Meta:
        model = CommentJourney
        fields = ['id', 'content']


class CommentJourneyDetailSerializers(serializers.ModelSerializer):
    user = UserSerializer()
    is_member = serializers.SerializerMethodField()

    def get_is_member(self, comment):
        journey = comment.journey
        return Participation.objects.filter(journey=journey, user=comment.user, is_approved=True).exists()

    class Meta:
        model = CommentJourney
        fields = ['user', 'id', 'content', 'created_date', 'is_member']


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer()

    class Meta:
        model = Notification
        fields = ['id', 'post_id', 'journey_id', 'message', 'read', 'actor']
