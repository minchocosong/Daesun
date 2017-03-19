from django.conf.urls import url
from django.contrib import admin
from . import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^cp/group$', views.cp_group, name='cp_group'),
    url(r'^cp/daily', views.cp_daily, name='cp_daily'),
    url(r'^shop$', views.shop, name='shop'),
    url(r'^timeline$', views.timeline, name='timeline'),
    url(r'^name$', views.name_chemistry, name='name_chemistry'),
    url(r'^pledge$', views.pledge, name='pledge'),
    url(r'^pledge/rank$', views.pledge_rank_api, name='pledge_rank'),
    url(r'^rating$', views.approval_rating, name='approval_rating'),
    url(r'^lovetest$', views.love_test, name='love_test'),
    url(r'^admin/', admin.site.urls),
    url(r'^sns$', views.get_candidate_sns_api, name='candidate_sns_api'),
    url(r'^issue$', views.get_issue_keyword_api, name='issue_keyword_api'),
    url(r'^cheering$', views.cheering_message_api, name='cheering_message'),
    url(r'^constellation$', views.constellation_api, name='constellation_api'),
    url(r'^blood$', views.blood_type_chemistry_api, name='blood_type_chemistry_api'),
    url(r'^lucky', views.save_lucky_result, name='save_lucky_result'),
    url(r'^luckyname$', views.lucky_name_chemistry, name='lucky_name_api'),
]
