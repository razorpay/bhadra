from django.urls import re_path, include

from dojo.user import views

urlpatterns = [
    # social-auth-django required url package
    re_path('', include('social_django.urls', namespace='social')),
    #  user specific
    re_path(r'^login$', views.login_view, name='login'),
    re_path(r'^adminlogin$', views.admin_login_view, name='admin_login'),
    re_path(r'^logout$', views.logout_view, name='logout'),
    re_path(r'^alerts$', views.alerts, name='alerts'),
    re_path(r'^alerts/json$', views.alerts_json, name='alerts_json'),
    re_path(r'^alerts/count$', views.alertcount, name='alertcount'),
    re_path(r'^delete_alerts$', views.delete_alerts, name='delete_alerts'),
    re_path(r'^profile$', views.view_profile, name='view_profile'),
    re_path(r'^change_password$', views.change_password,
        name='change_password'),
    re_path(r'^user$', views.user, name='users'),
    re_path(r'^user/add$', views.add_user, name='add_user'),
    re_path(r'^user/(?P<uid>\d+)$', views.view_user,
        name='view_user'),
    re_path(r'^user/(?P<uid>\d+)/edit$', views.edit_user,
        name='edit_user'),
    re_path(r'^user/(?P<uid>\d+)/delete', views.delete_user,
        name='delete_user'),
    re_path(r'^api/key-v2$', views.api_v2_key, name='api_v2_key'),
    re_path(r'^user/(?P<uid>\d+)/add_product_type_member$', views.add_product_type_member,
        name='add_product_type_member_user'),
    re_path(r'^user/(?P<uid>\d+)/add_product_member$', views.add_product_member,
        name='add_product_member_user'),
    re_path(r'^user/(?P<uid>\d+)/add_group_member$', views.add_group_member,
        name='add_group_member_user')
]
