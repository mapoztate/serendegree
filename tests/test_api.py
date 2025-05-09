import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import json
import io
import pandas as pd

from core.models import Course, Program, StudentSchedule

class TestAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test courses
        self.course1 = Course.objects.create(
            course_code="CS101",
            title="Intro to Programming",
            description="Basic concepts",
            institution="Test College",
            embedding=[1.0, 0.0, 0.0]
        )
        
        self.course2 = Course.objects.create(
            course_code="CS102",
            title="Data Structures",
            description="Advanced concepts",
            institution="Test College",
            embedding=[0.0, 1.0, 0.0]
        )
        
        # Create test program
        self.program = Program.objects.create(
            name="Computer Science",
            institution="Test University",
            description="CS Program",
            embedding=[0.707, 0.707, 0.0]
        )
        self.program.required_courses.add(self.course1, self.course2)

    def test_course_list(self):
        url = reverse('course-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_program_list(self):
        url = reverse('program-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_upload_courses_csv(self):
        url = reverse('course-upload-csv')
        
        # Create test CSV file
        df = pd.DataFrame({
            'course_code': ['CS103'],
            'title': ['Algorithms'],
            'description': ['Algorithm design'],
            'institution': ['Test College']
        })
        
        csv_file = io.StringIO()
        df.to_csv(csv_file, index=False)
        csv_file.seek(0)
        
        response = self.client.post(
            url,
            {'file': io.StringIO(csv_file.getvalue())},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Course.objects.filter(course_code='CS103').exists())

    def test_upload_schedule_csv(self):
        url = reverse('studentschedule-upload-schedule')
        
        # Create test CSV file
        df = pd.DataFrame({
            'course_code': ['CS101', 'CS102']
        })
        
        csv_file = io.StringIO()
        df.to_csv(csv_file, index=False)
        csv_file.seek(0)
        
        response = self.client.post(
            url,
            {'file': io.StringIO(csv_file.getvalue())},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schedule_id = response.data['schedule_id']
        schedule = StudentSchedule.objects.get(id=schedule_id)
        self.assertEqual(schedule.courses.count(), 2)

    def test_recommend_programs(self):
        # Create a schedule
        schedule = StudentSchedule.objects.create()
        schedule.courses.add(self.course1)
        schedule.embedding = [1.0, 0.0, 0.0]
        schedule.save()
        
        url = reverse('studentschedule-recommend-programs', args=[schedule.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should find one program
        self.assertEqual(response.data[0]['program']['id'], self.program.id)
