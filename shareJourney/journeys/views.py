from datetime import datetime, timedelta

from django.shortcuts import render
from django.utils.timezone import now, make_aware
from oauth2_provider.contrib.rest_framework import permissions
from rest_framework import viewsets, generics, parsers, status, permissions
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from journeys import serializers, perms, paginators
from journeys.models import User, Journey, Post, Comment, LikePost, LikeJourney, Notification, Participation, \
    CommentJourney, Report, ReportedUser, Follow
from journeys.serializers import NotificationSerializer, PostSerializer, PostDetailSerializer, \
    CommentJourneyDetailSerializers, ReportSerializer


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = User.objects.filter(is_active=True).all()
    serializer_class = serializers.UserDetailSerializer
    parser_classes = [parsers.MultiPartParser]

    def get_permissions(self):
        if self.action in ['current_user', 'get_followers', 'get_following', 'follow']:
            return [permissions.IsAuthenticated()]
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
        return Response(serializers.UserDetailSerializer(request.user).data)

    @action(methods=['get'], url_path='followers', detail=True)
    def get_followers(self, request, pk):
        followers = Follow.objects.filter(following=self.get_object(), is_active=True).all()
        serializer = serializers.UserSerializer([follow.follower for follow in followers], many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    @action(methods=['get'], url_path='following', detail=True)
    def get_following(self, request, pk):
        following = Follow.objects.filter(follower=self.get_object(), is_active=True).all()
        serializer = serializers.UserSerializer([follow.following for follow in following], many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    @action(methods=['post'], url_path='follow', detail=True)
    def follow(self, request, pk):

        follow, created = Follow.objects.get_or_create(follower=request.user, following=self.get_object())

        if not created:
            follow.is_active = not follow.is_active
            follow.save()

        return Response(status=status.HTTP_200_OK)


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()
    serializer_class = serializers.JourneyDetailSerializers
    pagination_class = paginators.JourneyPaginator
    permission_classes = [permissions.AllowAny()]

    def perform_create(self, serializer):  # khi gọi api create sẽ lấy user đang đăng nhập gán vào
        serializer.save(user_create=self.request.user)

    def get_permissions(self):
        if self.action in ['create', 'add_comment']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy', 'lock_comment', 'delete_participant',
                             'complete_journey']:
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
        serializer = PostDetailSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

    @action(methods=['post'], url_name='like', detail=True)
    def like(self, request, pk):
        journey = self.get_object()
        actor = request.user
        like, created = LikeJourney.objects.get_or_create(user=request.user, journey=self.get_object())
        if not created:
            like.active = not like.active
            like.save()
        if created and like.active:
            self.create_notification(journey, actor)
        return Response(status=status.HTTP_200_OK)

    def create_notification(self, journey, actor):
        Notification.objects.create(
            user=journey.user_create,
            journey=journey,
            message=f"{actor.last_name} đã thích hành trình của bạn.",
            actor=actor
        )

    # @action(detail=True, methods=['get'])
    # def likes_count(self, request, pk=None):
    #     journey = self.get_object()
    #     likes_count = LikeJourney.objects.filter(journey=journey, active=True).count()
    #     return Response({'journey_id': pk, 'likes_count': likes_count})

    @action(methods=['post'], url_name='add_comment', detail=True)
    def add_comment(self, request, pk):
        actor = request.user
        c = CommentJourney.objects.create(user=actor,
                                          journey=self.get_object(),
                                          content=request.data.get('content'))
        self.create_notificationCmt(c, actor)
        return Response(serializers.CommentJourneyDetailSerializers(c).data, status=status.HTTP_201_CREATED)

    def create_notificationCmt(self, commentJourney, actor):
        journey = commentJourney.journey
        Notification.objects.create(
            user=journey.user_create,
            journey=journey,
            message=f"{actor.last_name} đã bình luận trên hành trình của bạn.",
            actor=actor
        )

    @action(methods=['delete'], url_path=r'delete_comment/(?P<comment_pk>\d+)', url_name='delete_comment', detail=True)
    def delete_comment(self, request, pk, comment_pk):
        journey = self.get_object()
        comment = CommentJourney.objects.get(pk=comment_pk, journey=journey)
        if comment.user == request.user:
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'Bạn không có quyền xóa comment này.'}, status=status.HTTP_403_FORBIDDEN)

    @action(methods=['post'], detail=True, url_path='comment_reply')
    def reply_to_comment(self, request, pk=None):
        journey = self.get_object()
        comment_id = request.data.get('comment_id')
        content = request.data.get('content')

        try:
            comment = CommentJourney.objects.get(id=comment_id, journey=journey)
        except CommentJourney.DoesNotExist:
            return Response({"message": "Bình luận không tồn tại trong hành trình này."},
                            status=status.HTTP_404_NOT_FOUND)
        reply = CommentJourney.objects.create(
            user=request.user,
            journey=journey,
            content=content,
            parent_comment=comment
        )

        return Response({"message": "Đã trả lời bình luận thành công.", "reply_id": reply.id},
                        status=status.HTTP_201_CREATED)

    @action(methods=['patch'], url_path=r'update_comment/(?P<comment_pk>\d+)', url_name='update_comment', detail=True)
    def update_comment(self, request, pk, comment_pk):
        journey = self.get_object()
        comment = CommentJourney.objects.get(pk=comment_pk, journey=journey)
        serializer = serializers.CommentJourneySerializers(comment,
                                                           data=request.data)  # update ko dùng detail, nó yêu cầu user
        if comment.user == request.user:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)

    @action(methods=['patch'], url_name='lock_comment', detail=True)
    def lock_comment(self, request, pk):
        journey = self.get_object()
        journey.lock_cmt = True
        journey.save()
        return Response({'lock_cmt': journey.lock_cmt}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='approve_comment')
    def approve_comment(self, request, pk=None):
        journey = self.get_object()
        user = request.user
        comment_id = request.data.get('comment_id')
        try:
            comment = CommentJourney.objects.get(pk=comment_id, journey=journey)
        except CommentJourney.DoesNotExist:
            return Response({"message": "Bình luận không tồn tại hoặc không thuộc hành trình này."},
                            status=status.HTTP_400_BAD_REQUEST)
        if Participation.objects.filter(user=comment.user, journey=journey, is_approved=True).exists():
            return Response({"message": f"{comment.user.last_name} đã là thành viên của hành trình."},
                            status=status.HTTP_200_OK)
        Participation.objects.create(user=comment.user, journey=journey, is_approved=True)
        Notification.objects.create(
            user=comment.user,
            message=f"Bạn đã được {user.last_name} duyệt vào hành trình của họ."
        )
        return Response({"message": f"Bạn đã duyệt {comment.user.last_name} vào hành trình."},
                        status=status.HTTP_200_OK)

    @action(methods=['patch'], detail=True, url_path='delete_participant')
    def delete_participant(self, request, pk=None):
        journey = self.get_object()
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            participant = Participation.objects.get(journey=journey, user_id=user_id, is_approved=True)
        except Participation.DoesNotExist:
            return Response({"message": "Người dùng không tồn tại trong danh sách tham gia hoặc chưa được duyệt."},
                            status=status.HTTP_400_BAD_REQUEST)

        participant.is_approved = False
        participant.save()
        return Response({"message": f"{user.last_name} đã bị xóa khỏi hành trình."},
                        status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True, url_path='members')
    def get_members(self, request, pk=None):
        journey = self.get_object()
        participations = journey.participation_set.filter(is_approved=True).select_related('user')

        members = []
        member_data = {
            'id': journey.user_create.id,
            'ownerJourney': True,
            'full_name': journey.user_create.get_full_name(),
            'username': journey.user_create.username,
            'avatar': journey.user_create.avatar.url if journey.user_create.avatar else None,

        }
        members.append(member_data)
        for participation in participations:
            user = participation.user
            member_data = {
                'id': user.id,
                'full_name': user.get_full_name(),
                'username': user.username,
                'avatar': user.avatar.url if user.avatar else None,
            }
            members.append(member_data)  # đưa thành viên vào ds member để trả về
        return Response(members, status=status.HTTP_200_OK)

    @action(methods=['patch'], detail=True, url_path='complete_journey')
    def complete_journey(self, request, pk=None):
        journey = self.get_object()
        journey.active = False
        journey.save()
        return Response({"message": "Hành trình đã được hoàn thành."}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='rate_journey')
    def rate_journey(self, request, pk=None):
        journey = self.get_object()
        user = request.user
        rating = request.data.get('rating')

        if not rating:
            return Response({"message": "Vui lòng đánh giá."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            participation = Participation.objects.get(journey=journey, user=user, is_approved=True)
            participation.rating = rating
            participation.save()
            return Response({"message": "Đánh giá thành công."}, status=status.HTTP_200_OK)
        except Participation.DoesNotExist:
            return Response({"message": "Bạn không phải là thành viên của hành trình này."},
                            status=status.HTTP_403_FORBIDDEN)


class PostViewSet(viewsets.ViewSet, generics.RetrieveAPIView, generics.UpdateAPIView, generics.DestroyAPIView,
                  generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = serializers.PostSerializer
    permission_classes = [permissions.AllowAny()]

    def perform_create(self, serializer):  # user đăng bài
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['create', 'add_comment', 'like']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [perms.OwnerPostAuthenticated()]
        else:
            return [permissions.AllowAny()]

    @action(methods=['post'], url_name='add_comment', detail=True)
    def add_comment(self, request, pk):
        actor = request.user
        c = Comment.objects.create(user=actor,
                                   post=self.get_object(),
                                   content=request.data.get('content'))
        self.create_notificationCmt(c, actor)
        return Response(serializers.CommentDetailSerializers(c).data, status=status.HTTP_201_CREATED)

    def create_notificationCmt(self, comment, actor):
        post = comment.post
        Notification.objects.create(
            user=post.user,
            post=post,
            message=f"{actor.last_name} đã bình luận trên bài viết của bạn.",
            actor=actor
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

    @action(methods=['post'], detail=True, url_path='comment_reply')
    def reply_to_comment(self, request, pk=None):
        post = self.get_object()
        comment_id = request.data.get('comment_id')
        content = request.data.get('content')

        try:
            comment = Comment.objects.get(id=comment_id, post=post)
        except Comment.DoesNotExist:
            return Response({"message": "Bình luận không tồn tại trong hành trình này."},
                            status=status.HTTP_404_NOT_FOUND)
        reply = Comment.objects.create(
            user=request.user,
            post=post,
            content=content,
            parent_comment=comment
        )

        return Response({"message": "Đã trả lời bình luận thành công.", "reply_id": reply.id},
                        status=status.HTTP_201_CREATED)

    @action(methods=['post'], url_name='like', detail=True)
    def like(self, request, pk):
        post = self.get_object()
        user = request.user
        like, created = LikePost.objects.get_or_create(user=user, post=post)
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
            message=f"{user.last_name} đã thích bài viết của bạn.",
            actor=user
        )

    # @action(detail=True, methods=['get'])
    # def likes_count(self, request, pk=None):
    #     post = self.get_object()
    #     likes_count = LikePost.objects.filter(post=post, active=True).count()
    #     return Response({'post_id': pk, 'likes_count': likes_count})


# class NotificationViewSet(viewsets.ViewSet, generics.RetrieveAPIView):
#     queryset = Notification.objects.all()
#     serializer_class = NotificationSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def list(self, request):
#         user = request.user
#         notifications = Notification.objects.filter(user=user)
#         serializer = self.serializer_class(notifications, many=True)
#         return Response(serializer.data)
#
#     @action(methods=['get'], detail=True, url_path='redirect')
#     def redirect_to_object(self, request, pk=None):  # khi ấn vào 1 thông báo bất kỳ
#         notification = self.get_object()
#         if notification.post:
#             return Response({'post_id': notification.post_id}, status=status.HTTP_200_OK)
#         elif notification.journey:
#             return Response({'journey_id': notification.journey_id}, status=status.HTTP_200_OK)
#         else:
#             return Response({'error': 'Notification does not point to any object'}, status=status.HTTP_400_BAD_REQUEST)
#
#     # sau khi ấn vào 1 thông báo để xem chi tiết thì trả về id của thông báo đó để cập nhật đã xem và
#     # trả về id của post/journey để hiển thị nó
#     @action(methods=['post'], detail=True, url_path='mark_as_read')
#     def mark_as_read(self, request, pk=None):  # lấy post_id khi ấn vào xem 1 thông báo sẽ trả về post_id
#         notification = self.get_object()
#         notification.read = True
#         notification.save()
#         return Response({'message': 'Notification marked as read'}, status=status.HTTP_200_OK)


class CommentListAPIView(generics.ListAPIView):  # cmt của POST
    serializer_class = serializers.CommentDetailSerializers

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id)


class CommentJourneyListAPIView(generics.ListAPIView):
    serializer_class = CommentJourneyDetailSerializers

    def get_queryset(self):  # ds comment của 1 hành trình
        journey_id = self.kwargs['journey_id']
        return CommentJourney.objects.filter(journey_id=journey_id)


class UserJourneysListView(generics.ListAPIView):  # danh sách hành trình mà user tham gia
    serializer_class = serializers.JourneyDetailSerializers

    def get_queryset(self):
        user = self.request.user
        owned_journeys = Journey.objects.filter(user_create=user)
        participated_journeys = Participation.objects.filter(user=user, is_approved=True).values_list('journey',
                                                                                                      flat=True)
        return Journey.objects.filter(id__in=participated_journeys) | owned_journeys


class ReportViewSet(viewsets.ViewSet):
    serializer_class = ReportSerializer
    queryset = Report.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def report_user(self, request):
        reported_user_id = request.data.get('reported_user_id')
        reason = request.data.get('reason')
        if not reported_user_id or not reason:
            return Response({'error': 'Dữ liệu sai'}, status=status.HTTP_400_BAD_REQUEST)

        reported_user = User.objects.get(pk=reported_user_id)
        reported_user_profile, _ = ReportedUser.objects.get_or_create(
            user=reported_user)  # _ không quan tâm tới created như like
        reported_user_profile.report_count += 1
        reported_user_profile.save()

        Report.objects.get_or_create(
            reported_user=reported_user,
            reported_by=request.user,
            reason=reason,
            reported_user_profile=reported_user_profile
        )
        return Response({'message': 'Báo cáo thành công'}, status=status.HTTP_201_CREATED)


def index(request):
    return HttpResponse("Share Journey App")


def journey_statistics(request):
    total_journeys = Journey.objects.count()
    total_active_journeys = Journey.objects.filter(active=True).count()
    total_completed_journeys = Journey.objects.filter(active=False).count()

    today = now().date()
    start_of_month = today.replace(day=1)
    journeys_completed_this_month = Journey.objects.filter(active=False, updated_date__gte=start_of_month).count()

    context = {
        'total_journeys': total_journeys,
        'total_active_journeys': total_active_journeys,
        'total_completed_journeys': total_completed_journeys,
        'journeys_completed_this_month': journeys_completed_this_month,
    }

    return render(request, 'admin/statistics.html', context)


def journey_statistics_data(request):
    date_value = request.GET.get('date_value')

    try:
        date = make_aware(datetime.strptime(date_value, '%Y-%m'))
        start_of_period = date.replace(day=1)
        next_month = (start_of_period + timedelta(days=32)).replace(day=1)
        end_of_period = next_month

        total_journeys = Journey.objects.filter(created_date__gte=start_of_period,
                                                created_date__lt=end_of_period).count()
        total_active_journeys = Journey.objects.filter(created_date__gte=start_of_period,
                                                       created_date__lt=end_of_period, active=True).count()
        total_completed_journeys = Journey.objects.filter(updated_date__gte=start_of_period,
                                                          updated_date__lt=end_of_period, active=False).count()

        data = {
            'total_journeys': total_journeys,
            'total_active_journeys': total_active_journeys,
            'total_completed_journeys': total_completed_journeys,
        }

        return JsonResponse(data)
    except ValueError:
        return JsonResponse({'error': 'Invalid date value'}, status=400)
