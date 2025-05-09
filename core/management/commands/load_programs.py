from django.core.management.base import BaseCommand
import pandas as pd
from core.models import Course, Program
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Load programs from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file containing program data')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        
        try:
            # Read programs CSV
            programs_df = pd.read_csv(csv_file)
            programs_created = 0
            courses_associated = 0
            
            for _, row in programs_df.iterrows():
                # Create program if it doesn't exist
                program, created = Program.objects.get_or_create(
                    name=row['program_name'],
                    institution=row['institution'],
                    defaults={
                        'description': row.get('description', ''),
                        'degree_type': row.get('degree_level', 'Bachelor'),
                        'department': row.get('department', '')
                    }
                )
                
                if created:
                    programs_created += 1
                
                # Parse and associate required courses
                if 'required_courses' in row and pd.notna(row['required_courses']):
                    course_codes = [code.strip() for code in row['required_courses'].split(',')]
                    for code in course_codes:
                        courses = Course.objects.filter(course_code__icontains=code)
                        if courses.exists():
                            program.required_courses.add(*courses)
                            courses_associated += len(courses)
                        else:
                            logger.warning(f"Course {code} not found for program {program.name}")
                
                # Parse and associate elective courses if available
                if 'elective_courses' in row and pd.notna(row['elective_courses']):
                    course_codes = [code.strip() for code in row['elective_courses'].split(',')]
                    for code in course_codes:
                        courses = Course.objects.filter(course_code__icontains=code)
                        if courses.exists():
                            program.elective_courses.add(*courses)
                            courses_associated += len(courses)
                        else:
                            logger.warning(f"Elective course {code} not found for program {program.name}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully loaded {programs_created} new programs and associated {courses_associated} courses'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading programs: {str(e)}')
            )
            raise 