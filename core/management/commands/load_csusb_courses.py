from django.core.management.base import BaseCommand
import csv
from core.models import Course

class Command(BaseCommand):
    help = 'Load CSUSB courses from CSV file into database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file containing course data')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        courses_created = 0
        courses_updated = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Clean up the course code
                    course_code = row['course_code'].strip()
                    
                    # Create or update the course
                    course, created = Course.objects.update_or_create(
                        course_code=course_code,
                        institution=row['institution'],
                        defaults={
                            'title': row['title'],
                            'description': row['description']
                        }
                    )
                    
                    if created:
                        courses_created += 1
                    else:
                        courses_updated += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed courses: {courses_created} created, '
                    f'{courses_updated} updated'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading courses: {str(e)}')
            ) 