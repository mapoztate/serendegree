from django.core.management.base import BaseCommand
from core.embeddings.generator import update_course_embeddings, update_program_embeddings

class Command(BaseCommand):
    help = 'Update embeddings for all courses and programs'

    def handle(self, *args, **kwargs):
        self.stdout.write('Updating course embeddings...')
        update_course_embeddings()
        self.stdout.write(self.style.SUCCESS('Successfully updated course embeddings'))

        self.stdout.write('Updating program embeddings...')
        update_program_embeddings()
        self.stdout.write(self.style.SUCCESS('Successfully updated program embeddings')) 