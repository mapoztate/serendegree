from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, parser_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
import pandas as pd
from rest_framework.views import APIView
from django.conf import settings
import os

from .models import Course, Program, StudentSchedule
from .serializers import CourseSerializer, ProgramSerializer, StudentScheduleSerializer
from .embeddings.similarity import find_similar_programs, update_schedule_embedding, CourseRecommender
from .embeddings.gpt import generate_batch_explanations

# Template Views
class HomeView(TemplateView):
    template_name = 'core/home.html'

class UploadScheduleView(TemplateView):
    template_name = 'core/upload_schedule.html'

class AboutView(TemplateView):
    template_name = 'core/about.html'

# API ViewSets
class CourseViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    @action(detail=False, methods=['POST'])
    def upload_csv(self, request):
        """Upload courses from CSV file."""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        try:
            df = pd.read_csv(file)
            required_columns = ['course_code', 'title', 'description', 'institution']
            
            if not all(col in df.columns for col in required_columns):
                return Response(
                    {'error': 'CSV must contain: course_code, title, description, institution'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            courses = []
            for _, row in df.iterrows():
                course = Course(
                    course_code=row['course_code'],
                    title=row['title'],
                    description=row['description'],
                    institution=row['institution']
                )
                courses.append(course)

            Course.objects.bulk_create(courses)
            return Response({'message': f'Successfully uploaded {len(courses)} courses'})

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer

class StudentScheduleViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]
    queryset = StudentSchedule.objects.all()
    serializer_class = StudentScheduleSerializer
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['POST'], url_path='upload-schedule', url_name='upload-schedule')
    def upload_schedule(self, request):
        """Upload student schedule from CSV file."""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        try:
            df = pd.read_csv(file)
            if 'course_code' not in df.columns:
                return Response(
                    {'error': 'CSV must contain course_code column'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create new schedule
            schedule = StudentSchedule.objects.create()
            
            # Add courses to schedule
            course_codes = df['course_code'].tolist()
            courses = Course.objects.filter(course_code__in=course_codes)
            
            if not courses.exists():
                return Response(
                    {'error': 'No matching courses found in database'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            schedule.courses.set(courses)
            
            # Update schedule embedding
            try:
                update_schedule_embedding(schedule.id)
            except Exception as e:
                return Response(
                    {'error': f'Error updating schedule embedding: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response({
                'message': 'Schedule uploaded successfully',
                'schedule_id': schedule.id
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['GET'], url_path='recommend-programs', url_name='recommend_programs')
    def recommend_programs(self, request, pk=None):
        """Get program recommendations for a schedule."""
        try:
            schedule = self.get_object()
            
            # Get parameters from query string
            top_n = int(request.query_params.get('top_n', 5))
            min_similarity = float(request.query_params.get('min_similarity', 0.5))
            
            # Find similar programs
            matches = find_similar_programs(
                schedule,
                top_n=top_n,
                min_similarity=min_similarity
            )
            
            # Format matches for GPT
            match_dicts = [
                {'program': prog, 'similarity': sim}
                for prog, sim in matches
            ]
            
            # Generate explanations
            results = generate_batch_explanations(
                match_dicts,
                schedule.courses.all()
            )
            
            # Format response
            response_data = [{
                'program': ProgramSerializer(r['program']).data,
                'similarity_score': r['similarity'],
                'explanation': r['explanation']
            } for r in results]
            
            return Response(response_data)
            
        except StudentSchedule.DoesNotExist:
            return Response(
                {'error': 'Schedule not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CourseRecommendationView(APIView):
    def post(self, request):
        """
        Get course recommendations based on a list of course codes.
        
        Expected request format:
        {
            "courses": ["MATH-120", "ENGL-122", ...],
            "target_institution": "California State University, San Bernardino",
            "num_recommendations": 3  # optional, defaults to 3
        }
        """
        # Validate input
        course_codes = request.data.get('courses', [])
        target_institution = request.data.get('target_institution')
        num_recommendations = int(request.data.get('num_recommendations', 3))
        
        if not course_codes:
            return Response(
                {'error': 'No courses provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not target_institution:
            return Response(
                {'error': 'Target institution not specified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize recommender
        recommender = CourseRecommender()
        base_dir = settings.BASE_DIR
        input_files = [
            os.path.join(base_dir, 'sample_courses.csv'),
            os.path.join(base_dir, 'csusb_courses.csv')
        ]
        recommender.load_embeddings(input_files)
        
        # Get recommendations for each course
        all_recommendations = []
        for code in course_codes:
            course_key = f"Diablo Valley College_{code}"
            similar_courses = recommender.find_similar_courses(
                course_key,
                n=num_recommendations,
                target_institution=target_institution
            )
            
            if similar_courses:
                all_recommendations.append({
                    'source_course': code,
                    'recommendations': similar_courses
                })
        
        return Response(all_recommendations)

class ScheduleRecommendationView(APIView):
    def post(self, request):
        """
        Get program recommendations based on a complete schedule.
        
        Expected request format:
        {
            "schedule_id": 123,  # Optional, if schedule already exists
            "courses": ["MATH-120", "ENGL-122", ...],  # Required if no schedule_id
            "num_recommendations": 5  # optional, defaults to 5
        }
        """
        schedule_id = request.data.get('schedule_id')
        course_codes = request.data.get('courses', [])
        num_recommendations = int(request.data.get('num_recommendations', 5))
        
        # Get or create schedule
        if schedule_id:
            try:
                schedule = StudentSchedule.objects.get(id=schedule_id)
            except StudentSchedule.DoesNotExist:
                return Response(
                    {'error': 'Schedule not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            if not course_codes:
                return Response(
                    {'error': 'Either schedule_id or courses must be provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create new schedule
            schedule = StudentSchedule.objects.create()
            
            # Add courses to schedule
            courses = Course.objects.filter(
                course_code__in=course_codes,
                institution='Diablo Valley College'
            )
            schedule.courses.set(courses)
        
        # Get recommendations
        recommendations = []
        try:
            similar_programs = find_similar_programs(schedule, top_n=num_recommendations)
            
            for program, similarity in similar_programs:
                recommendations.append({
                    'program_name': program.name,
                    'institution': program.institution,
                    'similarity_score': float(similarity),
                    'description': program.description
                })
        except Exception as e:
            return Response(
                {'error': f'Error generating recommendations: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'schedule_id': schedule.id,
            'recommendations': recommendations
        })
