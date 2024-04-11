from django.contrib import admin
from django import forms
from ckeditor_uploader.widgets \
    import CKEditorUploadingWidget
from .models import User, Journey, VisitPoint, Participation, Post, Comment, Report


class PostForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = Post
        fields = '__all__'


class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'content', 'created_date', 'user']
    form = PostForm


class VisitPointInlineAdmin(admin.StackedInline):
    model = VisitPoint
    fk_name = 'journey'


class ParticipationInlineAdmin(admin.StackedInline):
    model = Participation
    fk_name = 'journey'


class JourneyAdmin(admin.ModelAdmin):
    search_fields = ['name_journey']
    inlines = [VisitPointInlineAdmin, ParticipationInlineAdmin, ]


class JourneyAppAdminSite(admin.AdminSite):
    site_title = 'Trang quản trị của tôi'
    site_header = 'Hệ thống Quản lý hành trình trực tuyến'
    index_title = 'Trang chủ quản trị'


admin_site = JourneyAppAdminSite(name='myjourney')
admin_site.register(Journey, JourneyAdmin)
admin_site.register(User)
admin_site.register(VisitPoint)
admin_site.register(Participation)
admin_site.register(Post,PostAdmin)
admin_site.register(Report)
