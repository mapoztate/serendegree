from django.core.management.base import BaseCommand
from core.models import Course
import pandas as pd
import os

class Command(BaseCommand):
    help = 'Load sample courses from CSV into database'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        sample_courses_path = os.path.join(base_dir, 'sample_courses.csv')
        
        if not os.path.exists(sample_courses_path):
            self.stdout.write(self.style.ERROR(f'File not found: {sample_courses_path}'))
            return
            
        try:
            df = pd.read_csv(sample_courses_path)
            courses_created = 0
            
            for _, row in df.iterrows():
                course_code = row['course_code'].strip('"')  # Remove quotes
                course, created = Course.objects.get_or_create(
                    course_code=course_code,
                    institution=row['institution'].strip('"'),
                    defaults={
                        'title': row['title'].strip('"'),
                        'description': row['description'].strip('"')
                    }
                )
                if created:
                    courses_created += 1
            
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {courses_created} courses'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading courses: {str(e)}')) 