from rest_framework import serializers
from .models import Course, Program, StudentSchedule

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'course_code', 'title', 'description', 'institution', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ProgramSerializer(serializers.ModelSerializer):
    required_courses = CourseSerializer(many=True, read_only=True)

    class Meta:
        model = Program
        fields = ['id', 'name', 'institution', 'description', 'required_courses', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class StudentScheduleSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)

    class Meta:
        model = StudentSchedule
        fields = ['id', 'courses', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        courses_data = self.context.get('courses', [])
        schedule = StudentSchedule.objects.create(**validated_data)
        schedule.courses.set(courses_data)
        return schedule 