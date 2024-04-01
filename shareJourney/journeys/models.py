from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    avatar = models.ImageField(upload_to='postImageUsers', blank=False)
    active = models.BooleanField(default=True)  # admin khóa tài khoản


class Journey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # người tạo hành trình
    start_location = models.CharField(max_length=100)
    end_location = models.CharField(max_length=100)
    created_date = models.DateTimeField(auto_now_add=True)
    departure_time = models.DateTimeField(auto_now_add=True)  # thời gian khởi hành
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s journey from {self.start_location} to {self.end_location}"


class Interaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    journey = models.ForeignKey(Journey, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Checkpoint(models.Model):
    journey = models.ForeignKey(Journey, related_name='checkpoints', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # 1 hành trình có nhieu điểm ghé qua
    estimated_duration_to_destination = models.DurationField(null=True,
                                                             blank=True)  # thời gian ước tính từ điểm hiện tại đến đích

    def __str__(self):
        return self.name


class Participation(Interaction):  # tạo ra bảng mới giữa User-journey
    joined_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)  # xác nhận người tham gia hành trình

    def __str__(self):
        return f"{self.user.username} joined {self.journey} at {self.joined_at}"


class Post(Interaction):
    content = models.TextField()
    image = models.ImageField(upload_to='postImageJourney', null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    lock_cmt = models.BooleanField(default=False)  # đóng khi đã đủ người tham gia

    def __str__(self):
        return f"Post by {self.user.username} created at {self.created_date}"


class Like(Interaction):
    class Meta:
        unique_together = ("journey", "user")


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)  # duyệt người tham gia

    def __str__(self):
        return f"Comment by {self.user.username} on post {self.post} at {self.created_date}"
