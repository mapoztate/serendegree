import pytest
from django.test import TestCase
from core.models import Course, Program, StudentSchedule
import numpy as np

class TestCourse(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            course_code="CS101",
            title="Introduction to Programming",
            description="Basic programming concepts",
            institution="Test College"
        )
        self.embedding = [0.1, 0.2, 0.3]
        self.course.embedding = self.embedding
        self.course.save()

    def test_course_creation(self):
        self.assertEqual(self.course.course_code, "CS101")
        self.assertEqual(self.course.title, "Introduction to Programming")
        self.assertEqual(self.course.institution, "Test College")

    def test_course_embedding(self):
        embedding_array = self.course.get_embedding_array()
        self.assertTrue(isinstance(embedding_array, np.ndarray))
        self.assertTrue(np.array_equal(embedding_array, np.array(self.embedding)))

class TestProgram(TestCase):
    def setUp(self):
        self.course1 = Course.objects.create(
            course_code="CS101",
            title="Intro to Programming",
            description="Basic concepts",
            institution="Test College"
        )
        self.course2 = Course.objects.create(
            course_code="CS102",
            title="Data Structures",
            description="Advanced concepts",
            institution="Test College"
        )
        self.program = Program.objects.create(
            name="Computer Science",
            institution="Test University",
            description="CS Program"
        )
        self.program.required_courses.add(self.course1, self.course2)

    def test_program_creation(self):
        self.assertEqual(self.program.name, "Computer Science")
        self.assertEqual(self.program.required_courses.count(), 2)

class TestStudentSchedule(TestCase):
    def setUp(self):
        self.course1 = Course.objects.create(
            course_code="CS101",
            title="Intro to Programming",
            description="Basic concepts",
            institution="Test College"
        )
        self.course2 = Course.objects.create(
            course_code="CS102",
            title="Data Structures",
            description="Advanced concepts",
            institution="Test College"
        )
        self.schedule = StudentSchedule.objects.create()
        self.schedule.courses.add(self.course1, self.course2)

    def test_schedule_creation(self):
        self.assertEqual(self.schedule.courses.count(), 2)
        self.assertIn(self.course1, self.schedule.courses.all())
        self.assertIn(self.course2, self.schedule.courses.all())
