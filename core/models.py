from django.db import models
import numpy as np

# Create your models here.

class Course(models.Model):
    course_code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    description = models.TextField()
    institution = models.CharField(max_length=100)
    embedding = models.JSONField(null=True, blank=True)  # Store embedding as JSON array
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course_code} - {self.title}"

    def get_embedding_array(self):
        """Convert JSON embedding to numpy array."""
        return np.array(self.embedding) if self.embedding else None

class Program(models.Model):
    DEGREE_TYPES = [
        ('Associate', 'Associate'),
        ('Bachelor', 'Bachelor'),
        ('Master', 'Master'),
        ('Doctorate', 'Doctorate'),
        ('Certificate', 'Certificate'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    institution = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    degree_type = models.CharField(max_length=20, choices=DEGREE_TYPES, default='Bachelor')
    required_courses = models.ManyToManyField(Course, related_name='required_for_programs')
    elective_courses = models.ManyToManyField(Course, related_name='elective_for_programs', blank=True)
    embedding = models.JSONField(null=True, blank=True)  # Aggregated embedding
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.degree_type}) - {self.institution}"

    def get_embedding_array(self):
        """Convert JSON embedding to numpy array."""
        return np.array(self.embedding) if self.embedding else None

class StudentSchedule(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    courses = models.ManyToManyField(Course)
    embedding = models.JSONField(null=True, blank=True)  # Aggregated embedding
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Schedule {self.id} created at {self.created_at}"

    def get_embedding_array(self):
        """Convert JSON embedding to numpy array."""
        return np.array(self.embedding) if self.embedding else None
