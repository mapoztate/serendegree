import pytest
import numpy as np
from django.test import TestCase
from core.models import Course, Program, StudentSchedule
from core.embeddings.loader import aggregate_embeddings
from core.embeddings.similarity import cosine_similarity, find_similar_programs

class TestEmbeddings(TestCase):
    def setUp(self):
        # Create test courses with embeddings
        self.course1 = Course.objects.create(
            course_code="CS101",
            title="Intro to Programming",
            description="Basic concepts",
            institution="Test College",
            embedding=[1.0, 0.0, 0.0]  # Simple unit vector
        )
        
        self.course2 = Course.objects.create(
            course_code="CS102",
            title="Data Structures",
            description="Advanced concepts",
            institution="Test College",
            embedding=[0.0, 1.0, 0.0]  # Orthogonal to course1
        )
        
        # Create a program with courses
        self.program = Program.objects.create(
            name="Computer Science",
            institution="Test University",
            description="CS Program",
            embedding=[0.707, 0.707, 0.0]  # 45 degrees between course1 and course2
        )
        self.program.required_courses.add(self.course1, self.course2)
        
        # Create a student schedule
        self.schedule = StudentSchedule.objects.create()
        self.schedule.courses.add(self.course1)
        self.schedule.embedding = [1.0, 0.0, 0.0]  # Same as course1
        self.schedule.save()

    def test_cosine_similarity(self):
        # Test similarity between orthogonal vectors (should be 0)
        sim = cosine_similarity(
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0])
        )
        self.assertEqual(sim, 0.0)
        
        # Test similarity between identical vectors (should be 1)
        sim = cosine_similarity(
            np.array([1.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0])
        )
        self.assertEqual(sim, 1.0)
        
        # Test similarity between 45-degree vectors
        sim = cosine_similarity(
            np.array([1.0, 0.0, 0.0]),
            np.array([0.707, 0.707, 0.0])
        )
        self.assertAlmostEqual(sim, 0.707, places=3)

    def test_aggregate_embeddings(self):
        embeddings = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0])
        ]
        
        aggregated = aggregate_embeddings(embeddings)
        expected = np.array([0.5, 0.5, 0.0])
        
        self.assertTrue(np.allclose(aggregated, expected))

    def test_find_similar_programs(self):
        # Should find the program with 0.707 similarity
        matches = find_similar_programs(self.schedule, top_n=1, min_similarity=0.5)
        
        self.assertEqual(len(matches), 1)
        program, similarity = matches[0]
        
        self.assertEqual(program.id, self.program.id)
        self.assertAlmostEqual(similarity, 0.707, places=3)
