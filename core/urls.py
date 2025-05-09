from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'courses', views.CourseViewSet)
router.register(r'programs', views.ProgramViewSet)
router.register(r'schedules', views.StudentScheduleViewSet, basename='schedules')

app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
    path('recommend/courses/', views.CourseRecommendationView.as_view(), name='recommend_courses'),
    path('recommend/programs/', views.ScheduleRecommendationView.as_view(), name='recommend_programs'),
] 