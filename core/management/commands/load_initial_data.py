from django.core.management.base import BaseCommand
import pandas as pd
from core.models import Course, Program

class Command(BaseCommand):
    help = 'Load initial data for testing'

    def handle(self, *args, **kwargs):
        # Load courses
        courses_df = pd.read_csv('sample_courses.csv')
        for _, row in courses_df.iterrows():
            Course.objects.get_or_create(
                course_code=row['course_code'],
                defaults={
                    'title': row['title'],
                    'description': row['description'],
                    'institution': row['institution']
                }
            )
        self.stdout.write(self.style.SUCCESS('Successfully loaded courses'))

        # Load programs
        programs_df = pd.read_csv('sample_programs.csv')
        for _, row in programs_df.iterrows():
            program, _ = Program.objects.get_or_create(
                name=row['name'],
                institution=row['institution'],
                defaults={
                    'description': row['description']
                }
            )
            
            # Associate relevant courses with programs
            if program.name == 'Computer Science':
                program.required_courses.add(
                    *Course.objects.filter(course_code__in=['CS101', 'MATH101'])
                )
            elif program.name == 'Biology':
                program.required_courses.add(
                    *Course.objects.filter(course_code__in=['BIOL110', 'CHEM110'])
                )
            elif program.name == 'Psychology':
                program.required_courses.add(
                    *Course.objects.filter(course_code__in=['PSYC100', 'BIOL110'])
                )
            elif program.name == 'Mathematics':
                program.required_courses.add(
                    *Course.objects.filter(course_code__in=['MATH101', 'PHYS101'])
                )
            elif program.name == 'Physics':
                program.required_courses.add(
                    *Course.objects.filter(course_code__in=['PHYS101', 'MATH101'])
                )
            elif program.name == 'Economics':
                program.required_courses.add(
                    *Course.objects.filter(course_code__in=['ECON101', 'MATH101'])
                )
            elif program.name == 'Philosophy':
                program.required_courses.add(
                    *Course.objects.filter(course_code__in=['PHIL101', 'ENGL101'])
                )
            elif program.name == 'English Literature':
                program.required_courses.add(
                    *Course.objects.filter(course_code__in=['ENGL101', 'PHIL101'])
                )

        self.stdout.write(self.style.SUCCESS('Successfully loaded programs')) 