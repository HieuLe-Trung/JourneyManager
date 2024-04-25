from oauth2_provider.contrib.rest_framework import permissions
from rest_framework import viewsets, generics, parsers, status, permissions
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from journeys import serializers, perms, paginators
from journeys.models import User, Journey, Post, Comment, LikePost, LikeJourney, Notification, Participation
from journeys.serializers import NotificationSerializer, PostSerializer


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = User.objects.filter(is_active=True).all()
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

    def get_permissions(self):
        if self.action.__eq__('current_user'):
            return [perms.OwnerPostAuthenticated()]
        return [permissions.AllowAny()]

    # lấy thông tin người đang đăng nhập để hiển thị profile
    @action(methods=['get', 'patch', 'delete'], url_name='current_user', detail=False)
    def current_user(self, request):
        if request.method == 'PATCH':
            user = request.user
            serializer = self.get_serializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            user = request.user
            user.is_active = False
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializers.UserSerializer(request.user).data)


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.filter(active=True).all()
    serializer_class = serializers.JourneyDetailSerializers
    pagination_class = paginators.JourneyPaginator
    permission_classes = [permissions.AllowAny()]

    def perform_create(self, serializer):  # khi gọi api create sẽ lấy user đang đăng nhập gán vào
        serializer.save(user_create=self.request.user)

    def get_permissions(self):
        if self.action in ['create', 'register_participation']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [perms.OwnerAuthenticated()]
        else:
            return [permissions.AllowAny()]

    def get_queryset(self):
        queries = self.queryset

        q = self.request.query_params.get("q")  # khi search /?q=... thì lấy giá trị q về
        if q:
            queries = queries.filter(name_journey__icontains=q)

        return queries

    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        journey = self.get_object()
        posts = Post.objects.filter(journey=journey)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    @action(methods=['post'], url_name='like', detail=True)
    def like(self, request, pk):
        journey = self.get_object()
        user = request.user
        like, created = LikeJourney.objects.get_or_create(user=request.user, journey=self.get_object())
        if not created:
            like.active = not like.active
            like.save()
        if created and like.active:
            self.create_notification(journey, user)
        return Response(status=status.HTTP_200_OK)

    def create_notification(self, journey, user):
        Notification.objects.create(
            user=journey.user_create,
            journey=journey,
            message=f"{user.last_name} đã thích hành trình của bạn."
        )

    @action(detail=True, methods=['get'])
    def likes_count(self, request, pk=None):
        journey = self.get_object()
        likes_count = LikeJourney.objects.filter(journey=journey, active=True).count()
        return Response({'journey_id': pk, 'likes_count': likes_count})

    # đăng ký tham gia hành trình
    @action(detail=True, methods=['post'], url_path='register')
    def register_participation(self, request, pk=None):
        journey = self.get_object()
        user = request.user
        participation = Participation.objects.create(user=user, journey=journey)
        self.create_notificationRegister(journey.user_create, participation)
        return Response({"message": "Yêu cầu tham gia đã được gửi."}, status=status.HTTP_201_CREATED)

    def create_notificationRegister(self, user, participation):
        notification_message = f"{participation.user.last_name} đã đăng ký tham gia hành trình của bạn."
        Notification.objects.create(user=user, message=notification_message, participation=participation)


class PostViewSet(viewsets.ViewSet, generics.RetrieveAPIView, generics.UpdateAPIView, generics.DestroyAPIView,
                  generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = serializers.PostDetailSerializer
    permission_classes = [permissions.AllowAny()]

    def perform_create(self, serializer):  # user đăng bài
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['create', 'add_comment', 'like']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy', 'lock_comment']:
            return [perms.OwnerPostAuthenticated()]
        else:
            return [permissions.AllowAny()]

    @action(methods=['post'], url_name='add_comment', detail=True)
    def add_comment(self, request, pk):
        c = Comment.objects.create(user=request.user,
                                   post=self.get_object(),
                                   content=request.data.get('content'))
        self.create_notificationCmt(c)
        return Response(serializers.CommentDetailSerializers(c).data, status=status.HTTP_201_CREATED)

    def create_notificationCmt(self, comment):
        post = comment.post
        user = comment.user
        Notification.objects.create(
            user=post.user,
            post=post,
            message=f"{user.last_name} đã bình luận trên bài viết của bạn."
        )

    @action(methods=['delete'], url_path=r'delete_comment/(?P<comment_pk>\d+)', url_name='delete_comment', detail=True)
    def delete_comment(self, request, pk, comment_pk):
        post = self.get_object()
        comment = Comment.objects.get(pk=comment_pk, post=post)
        if comment.user == request.user:
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'Bạn không có quyền xóa comment này.'}, status=status.HTTP_403_FORBIDDEN)

    @action(methods=['patch'], url_path=r'update_comment/(?P<comment_pk>\d+)', url_name='update_comment', detail=True)
    def update_comment(self, request, pk, comment_pk):
        post = self.get_object()
        comment = Comment.objects.get(pk=comment_pk, post=post)
        serializer = serializers.CommentSerializers(comment,
                                                    data=request.data)  # update ko dùng detail, nó yêu cầu user
        if comment.user == request.user:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

    @action(methods=['post'], url_name='like', detail=True)
    def like(self, request, pk):
        post = self.get_object()
        user = request.user
        like, created = LikePost.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.active = not like.active
            like.save()
        if created and like.active:
            self.create_notification(post, user)
        return Response(status=status.HTTP_200_OK)

    def create_notification(self, post, user):
        Notification.objects.create(
            user=post.user,
            post=post,
            message=f"{user.last_name} đã thích bài viết của bạn."
        )

    @action(detail=True, methods=['get'])
    def likes_count(self, request, pk=None):
        post = self.get_object()
        likes_count = LikePost.objects.filter(post=post, active=True).count()
        return Response({'post_id': pk, 'likes_count': likes_count})

    @action(methods=['post'], url_name='lock_comment', detail=True)
    def lock_comment(self, request, pk):
        post = self.get_object()
        post.lock_cmt = True
        post.save()
        return Response(status=status.HTTP_200_OK)


class NotificationViewSet(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user = request.user
        notifications = Notification.objects.filter(user=user)
        serializer = self.serializer_class(notifications, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=True, url_path='redirect')
    def redirect_to_object(self, request, pk=None):  # khi ấn vào 1 thông báo bất kỳ
        notification = self.get_object()
        if notification.post:
            return Response({'post_id': notification.post_id}, status=status.HTTP_200_OK)
        elif notification.journey:
            return Response({'journey_id': notification.journey_id}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Notification does not point to any object'}, status=status.HTTP_400_BAD_REQUEST)

    # sau khi ấn vào 1 thông báo để xem chi tiết thì trả về id của thông báo đó để cập nhật đã xem và
    # trả về id của post/journey để hiển thị nó
    @action(methods=['post'], detail=True, url_path='mark_as_read')
    def mark_as_read(self, request, pk=None):  # lấy post_id khi ấn vào xem 1 thông báo sẽ trả về post_id
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'message': 'Notification marked as read'}, status=status.HTTP_200_OK)


class CommentListAPIView(generics.ListAPIView):
    serializer_class = serializers.CommentDetailSerializers

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id)


def index(request):
    return HttpResponse("Share Journey App")
