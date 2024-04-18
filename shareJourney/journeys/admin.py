from cloudinary.models import CloudinaryResource
from django.contrib import admin
from django.utils.html import mark_safe

from .models import User, Journey, VisitPoint, Participation, Post, Comment, Report, Image, LikePost


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'is_active']
    readonly_fields = ['img']

    # def img(self, user):
    #     if user:
    #         return mark_safe(
    #             '<img src="/static/{url}" width="240" />' \
    #                 .format(url=user.avatar.name)
    #         )
    def img(self, obj):
        if obj.avatar:
            if type(obj.avatar) is CloudinaryResource:
                return mark_safe(
                    f'<img src="{obj.avatar.url}" height="200" alt="avatar" />'
                )
            return mark_safe(
                f'<img src="{obj.avatar.name}" height="200" alt="avatar" />'
            )


class VisitPointInlineAdmin(admin.StackedInline):
    model = VisitPoint
    fk_name = 'journey'


class ImageInlineAdmin(admin.StackedInline):
    model = Image
    fk_name = 'post'


class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'content', 'created_date', 'user']
    inlines = [ImageInlineAdmin, ]
    # readonly_fields = ['imagePost']
    #
    # def imagePost(self, post):  # ĐANG GẶP LỖI HIỂN THỊ ẢNH
    #     if post.images.exists():
    #         images_html = ''
    #         for image in post.images.all():
    #             images_html += f'<img src="{image.image.url}" width="100"/>'
    #         return mark_safe(images_html)
    #     else:
    #         return 'No images'


class ParticipationInlineAdmin(admin.StackedInline):
    model = Participation
    fk_name = 'journey'


class ParticipationAdmin(admin.ModelAdmin):
    list_display = ['id', 'journey']


class JourneyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name_journey', 'created_date', 'start_location', 'end_location', 'active', 'user_create']
    search_fields = ['name_journey']
    inlines = [VisitPointInlineAdmin, ParticipationInlineAdmin, ]


# class ImageAdmin(admin.ModelAdmin):
#     list_display = ['id', 'imgs']
#     readonly_fields = ['imgs']
#
#     def imgs(self, image):  # truyền obj của model
#         if image:
#             return mark_safe(
#                 '<img src="/static/{url}" width="100" />' \
#                     .format(url=image.image.name)
#             )

class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'content', 'created_date']


class JourneyAppAdminSite(admin.AdminSite):
    site_title = 'Trang quản trị của tôi'
    site_header = 'Hệ thống Quản lý hành trình trực tuyến'
    index_title = 'Trang chủ quản trị'


admin_site = JourneyAppAdminSite(name='myjourney')

admin_site.register(Journey, JourneyAdmin)
admin_site.register(User, UserAdmin)
admin_site.register(VisitPoint)
admin_site.register(Participation, ParticipationAdmin)
admin_site.register(Post,PostAdmin)
admin_site.register(Comment,CommentAdmin)
admin_site.register(LikePost)
admin_site.register(Report)
admin_site.register(Image)
