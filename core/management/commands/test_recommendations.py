from django.core.management.base import BaseCommand
from core.models import Course, Program, StudentSchedule
from core.embeddings.similarity import find_similar_programs
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict

class Command(BaseCommand):
    help = 'Test recommendation accuracy with different schedule sizes'

    def create_schedule(self, courses):
        """Create a schedule with given courses."""
        schedule = StudentSchedule.objects.create()
        schedule.courses.set(courses)
        return schedule

    def analyze_recommendations(self, schedule, expected_program_name="Computer Science"):
        """Analyze recommendations for a schedule."""
        recommendations = find_similar_programs(schedule, top_n=10, min_similarity=0.0)
        
        # Find position of expected program
        position = -1
        for i, (program, score) in enumerate(recommendations):
            if program.name == expected_program_name:
                position = i + 1
                break
        
        return {
            'num_courses': schedule.courses.count(),
            'top_programs': [(p.name, f"{s:.3f}") for p, s in recommendations[:5]],
            'expected_program_position': position,
            'expected_program_score': next((s for p, s in recommendations if p.name == expected_program_name), None),
            'top_5_scores': [float(s) for _, s in recommendations[:5]]  # Store top 5 scores for analysis
        }

    def plot_results(self, all_results, output_path='recommendation_analysis.png'):
        """Plot analysis results."""
        # Prepare data for plotting
        df = pd.DataFrame(all_results)
        
        # Create figure with multiple subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: CS Program Score vs Number of Courses
        ax1.plot(df['num_courses'], df['expected_program_score'], 'bo-', label='CS Program Score')
        ax1.set_xlabel('Number of Courses')
        ax1.set_ylabel('CS Program Score')
        ax1.set_title('CS Program Score vs Number of Courses')
        ax1.grid(True)
        ax1.legend()

        # Plot 2: Top 5 Program Scores Distribution
        box_data = []
        course_nums = []
        for result in all_results:
            box_data.append(result['top_5_scores'])
            course_nums.extend([result['num_courses']] * 5)
        
        ax2.boxplot(box_data, labels=df['num_courses'].unique())
        ax2.set_xlabel('Number of Courses')
        ax2.set_ylabel('Score')
        ax2.set_title('Distribution of Top 5 Program Scores')
        ax2.grid(True)

        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

        self.stdout.write(f"Analysis plots saved to {output_path}")

    def handle(self, *args, **options):
        # Get all CS courses
        cs_courses = list(Course.objects.filter(course_code__startswith='CSE').order_by('course_code'))
        
        # Test different schedule sizes
        schedule_sizes = [1, 2, 3, 4, 5, 7, 10]
        all_results = []
        
        # Run multiple trials for each size to get average performance
        num_trials = 5
        
        self.stdout.write("\nTesting with increasing number of random CS courses:")
        for size in schedule_sizes:
            size_results = []
            for trial in range(num_trials):
                # Create schedule with random courses
                courses = list(np.random.choice(cs_courses, size=size, replace=False))
                schedule = self.create_schedule(courses)
                result = self.analyze_recommendations(schedule)
                size_results.append(result)
                
                self.stdout.write(f"\nTrial {trial + 1} - Schedule with {size} course(s):")
                self.stdout.write(f"Courses: {', '.join(c.course_code for c in courses)}")
                self.stdout.write(f"Top 5 programs: {result['top_programs']}")
                self.stdout.write(f"CS program position: {result['expected_program_position']}")
                self.stdout.write(f"CS program score: {result['expected_program_score']:.3f}")
                
                schedule.delete()
            
            # Average results for this size
            avg_result = {
                'num_courses': size,
                'expected_program_score': np.mean([r['expected_program_score'] for r in size_results]),
                'top_5_scores': [score for r in size_results for score in r['top_5_scores']]
            }
            all_results.append(avg_result)
        
        # Plot the results
        self.plot_results(all_results)
        
        # Print summary statistics
        self.stdout.write("\nSummary Statistics:")
        for result in all_results:
            self.stdout.write(f"\nNumber of Courses: {result['num_courses']}")
            self.stdout.write(f"Average CS Program Score: {result['expected_program_score']:.3f}")
            self.stdout.write(f"Average Top 5 Score: {np.mean(result['top_5_scores']):.3f}")
            self.stdout.write(f"Std Dev of Top 5 Score: {np.std(result['top_5_scores']):.3f}")
        
        # Core CS courses that should give strong signal
        core_courses = Course.objects.filter(
            course_code__in=['CSE 2010', 'CSE 2020', 'CSE 2130', 'CSE 4310']
        )
        
        self.stdout.write("\nTesting with core CS courses:")
        # Test with core courses
        schedule = self.create_schedule(core_courses)
        result = self.analyze_recommendations(schedule)
        
        self.stdout.write(f"\nSchedule with {core_courses.count()} core courses:")
        self.stdout.write(f"Courses: {', '.join(c.course_code for c in core_courses)}")
        self.stdout.write(f"Top 5 programs: {result['top_programs']}")
        self.stdout.write(f"CS program position: {result['expected_program_position']}")
        self.stdout.write(f"CS program score: {result['expected_program_score']:.3f}")
        
        schedule.delete()
        
        # Test with mixed courses (core + random)
        self.stdout.write("\nTesting with mixed core and random CS courses:")
        mixed_courses = list(core_courses)
        remaining_courses = [c for c in cs_courses if c not in core_courses]
        mixed_courses.extend(np.random.choice(remaining_courses, size=3, replace=False))
        
        schedule = self.create_schedule(mixed_courses)
        result = self.analyze_recommendations(schedule)
        
        self.stdout.write(f"\nSchedule with {len(mixed_courses)} mixed courses:")
        self.stdout.write(f"Courses: {', '.join(c.course_code for c in mixed_courses)}")
        self.stdout.write(f"Top 5 programs: {result['top_programs']}")
        self.stdout.write(f"CS program position: {result['expected_program_position']}")
        self.stdout.write(f"CS program score: {result['expected_program_score']:.3f}")
        
        schedule.delete() 