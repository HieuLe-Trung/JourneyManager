from cloudinary.models import CloudinaryResource
from django.contrib import admin
from django.utils.html import mark_safe
from .models import User, Journey, Participation, Post, Comment, Report, Image, CommentJourney


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'is_active']
    readonly_fields = ['img']

    def img(self, obj):
        if obj.avatar:
            if type(obj.avatar) is CloudinaryResource:
                return mark_safe(
                    f'<img src="{obj.avatar.url}" height="200" alt="avatar" />'
                )
            return mark_safe(
                f'<img src="{obj.avatar.name}" height="200" alt="avatar" />'
            )


class ImageInlineAdmin(admin.StackedInline):
    model = Image
    fk_name = 'post'


class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'content', 'created_date', 'user']
    inlines = [ImageInlineAdmin, ]


class ParticipationInlineAdmin(admin.StackedInline):
    model = Participation
    fk_name = 'journey'


class ParticipationAdmin(admin.ModelAdmin):
    list_display = ['id', 'journey']


class JourneyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name_journey', 'created_date', 'start_location', 'end_location', 'active', 'user_create']
    search_fields = ['name_journey']
    inlines = [ParticipationInlineAdmin, ]


class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'content', 'created_date']


class JourneyAppAdminSite(admin.AdminSite):
    site_title = 'Trang quản trị của tôi'
    site_header = 'Hệ thống Quản lý hành trình trực tuyến'
    index_title = 'Trang chủ quản trị'


admin_site = JourneyAppAdminSite(name='myjourney')

admin_site.register(Journey, JourneyAdmin)
admin_site.register(User, UserAdmin)
admin_site.register(Participation, ParticipationAdmin)
admin_site.register(Post, PostAdmin)
admin_site.register(Comment, CommentAdmin)
admin_site.register(CommentJourney, CommentAdmin)
admin_site.register(Report)
