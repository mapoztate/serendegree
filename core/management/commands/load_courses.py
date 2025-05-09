from django.core.management.base import BaseCommand
from core.models import Course
from core.embeddings.course_embeddings import generate_course_embeddings
import pandas as pd
import os

class Command(BaseCommand):
    help = 'Load courses from CSV files and generate embeddings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regenerate embeddings even if they exist',
        )

    def handle(self, *args, **options):
        self.stdout.write('Loading courses and generating embeddings...')
        
        # Get base directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        # Define input files
        input_files = [
            os.path.join(base_dir, 'sample_courses.csv'),
            os.path.join(base_dir, 'csusb_courses.csv')
        ]
        
        # Check if files exist
        for file in input_files:
            if not os.path.exists(file):
                self.stdout.write(self.style.ERROR(f'File not found: {file}'))
                return
        
        # Generate embeddings
        try:
            embeddings = generate_course_embeddings(input_files)
            self.stdout.write(self.style.SUCCESS(f'Generated embeddings for {len(embeddings)} courses'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating embeddings: {str(e)}'))
            return
        
        # Load courses into database
        courses_created = 0
        courses_updated = 0
        
        for file in input_files:
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                course_key = f"{row['institution']}_{row['course_code']}"
                
                try:
                    course, created = Course.objects.update_or_create(
                        course_code=row['course_code'],
                        institution=row['institution'],
                        defaults={
                            'title': row['title'],
                            'description': row['description'],
                            'embedding': embeddings.get(course_key)
                        }
                    )
                    
                    if created:
                        courses_created += 1
                    else:
                        courses_updated += 1
                        
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'Error processing course {course_key}: {str(e)}'
                    ))
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed courses: {courses_created} created, {courses_updated} updated'
        )) 