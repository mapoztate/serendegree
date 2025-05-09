from django.core.management.base import BaseCommand
from core.models import Program, Course

class Command(BaseCommand):
    help = 'Update Computer Science program requirements with typical courses'

    def handle(self, *args, **kwargs):
        try:
            # Core CS courses that should be required
            core_courses = [
                'CSE 1250',  # Programming Basics
                'CSE 2010',  # Computer Science I
                'CSE 2020',  # Computer Science II
                'CSE 2130',  # Machine Organization
                'CSE 3100',  # Digital Logic
                'CSE 4010',  # Contemporary Computer Architecture
                'CSE 4100',  # Computer Networking and Security
                'CSE 4310',  # Algorithm Analysis
                'CSE 4550',  # Software Engineering
                'CSE 4600',  # Operating Systems
                'CSE 5000',  # Introduction to Formal Languages
                'CSE 5720',  # Database Systems
            ]
            
            # Elective courses that provide specialization
            elective_courses = [
                'CSE 4050',  # Web Application Development
                'CSE 4200',  # Computer Graphics
                'CSE 4400',  # Game Design
                'CSE 4410',  # Game Programming
                'CSE 4500',  # Platform Computing
                'CSE 5120',  # Introduction to Artificial Intelligence
                'CSE 5160',  # Machine Learning
                'CSE 5250',  # Parallel Algorithms and Programming
                'CSE 5350',  # Numerical Computation
                'CSE 5700',  # Compilers
            ]
            
            # Get the Computer Science program
            cs_program = Program.objects.get(
                name='Computer Science',
                degree_type='Bachelor',
                institution='California State University, San Bernardino'
            )
            
            # Add required courses
            required_courses = Course.objects.filter(course_code__in=core_courses)
            cs_program.required_courses.set(required_courses)
            
            # Add elective courses
            elective_courses = Course.objects.filter(course_code__in=elective_courses)
            cs_program.elective_courses.set(elective_courses)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated Computer Science program with '
                    f'{required_courses.count()} required courses and '
                    f'{elective_courses.count()} elective courses'
                )
            )
            
        except Program.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Computer Science program not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating program: {str(e)}')
            ) 