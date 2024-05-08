from cloudinary.models import CloudinaryField
from django.db import models
from django.contrib.auth.models import AbstractUser


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    # avatar = models.ImageField(upload_to="avatarJourney", null=True)
    is_active = models.BooleanField(default=True)  # admin khóa tài khoản
    avatar = CloudinaryField(folder="avatarJourney", null=False, blank=False, default='')
    phone = models.CharField(max_length=10, unique=True, null=True)
    email = models.EmailField(max_length=50, unique=True)


class Journey(BaseModel):
    user_create = models.ForeignKey(User, on_delete=models.CASCADE)  # người tạo hành trình
    name_journey = models.CharField(max_length=100, blank=False, null=False, default='')
    background = models.CharField(max_length=255, blank=True, null=True)
    lock_cmt = models.BooleanField(default=False)  # đóng khi đã đủ người tham gia
    start_location = models.CharField(max_length=100)
    end_location = models.CharField(max_length=100)
    # departure_time = models.DateTimeField(null=True, blank=True)  # thời gian khởi hành
    departure_time = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True)
    distance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estimated_time = models.DurationField(blank=True, null=True)

    def __str__(self):
        return self.name_journey


class Interaction(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    journey = models.ForeignKey(Journey, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Participation(Interaction):  # ds user tham gia hành trình
    joined_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)  # xác nhận người tham gia hành trình
    rating = models.IntegerField(null=True, blank=True)
    current_location = models.CharField(max_length=100, null=True)


class Post(Interaction):
    content = models.TextField()
    visit_point = models.CharField(max_length=255, blank=True, null=True)
    estimated_time_of_arrival = models.CharField(max_length=100, blank=True, null=True)


class Image(models.Model):
    image = CloudinaryField(folder="PostJourney", null=True, blank=True)
    post = models.ForeignKey(Post, related_name='images', on_delete=models.CASCADE, default=None)


class InteractionPost(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, default='')

    class Meta:
        abstract = True


class LikeJourney(Interaction):
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("journey", "user")


class LikePost(InteractionPost):
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("post", "user")


class CommentJourney(Interaction):
    content = models.TextField()
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')


class Comment(InteractionPost):
    content = models.TextField()
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')


class Report(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reporter = models.ForeignKey(User, related_name='reports_given', on_delete=models.CASCADE)
    reason = models.TextField()


class Notification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # gửi thông báo về cho ai
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    journey = models.ForeignKey(Journey, on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=255)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return self.message
