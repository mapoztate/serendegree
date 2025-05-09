import numpy as np
from typing import List, Tuple, Optional, Dict
from ..models import Program, StudentSchedule, Course
from .loader import aggregate_embeddings
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
from .course_embeddings import generate_course_embeddings
import pandas as pd
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    """
    if len(v1.shape) == 1:
        v1 = v1.reshape(1, -1)
    if len(v2.shape) == 1:
        v2 = v2.reshape(1, -1)
    return float(sklearn_cosine_similarity(v1, v2)[0][0])

def compute_weighted_embedding(embeddings: List[np.ndarray], weights: Optional[List[float]] = None) -> np.ndarray:
    """
    Compute weighted average of embeddings.
    
    Args:
        embeddings: List of embedding vectors
        weights: Optional weights for each embedding (e.g., course credits)
    """
    if not embeddings:
        return None
        
    if weights is None:
        weights = [1.0] * len(embeddings)
    
    # Normalize weights
    weights = np.array(weights) / sum(weights)
    
    # Stack embeddings and compute weighted average
    stacked = np.vstack(embeddings)
    return np.average(stacked, axis=0, weights=weights)

def find_similar_programs(
    schedule: StudentSchedule,
    top_n: int = 5,
    min_similarity: float = 0.3
) -> List[Tuple[Program, float]]:
    """
    Find programs most similar to a student's schedule.
    
    Args:
        schedule: StudentSchedule instance
        top_n: Number of top matches to return
        min_similarity: Minimum similarity threshold
        
    Returns:
        List of (program, similarity_score) tuples
    """
    # Get schedule courses and their embeddings
    schedule_courses = schedule.courses.all()
    course_embeddings = []
    course_weights = []  # Could be based on credits or other factors
    
    logger.info(f"Processing schedule with {schedule_courses.count()} courses")
    
    # Check if courses are from CSUSB
    is_csusb = any(course.course_code.startswith('CSE') for course in schedule_courses)
    
    for course in schedule_courses:
        if course.embedding:
            course_embeddings.append(course.get_embedding_array())
            course_weights.append(1.0)  # Could be course.credits if available
        else:
            logger.warning(f"Course {course.course_code} has no embedding")
    
    if not course_embeddings:
        logger.error("No course embeddings found for schedule")
        return []
    
    # Compute weighted schedule embedding
    schedule_embedding = compute_weighted_embedding(course_embeddings, course_weights)
    
    # Get all programs and compute similarities
    programs = Program.objects.all()
    similarities = []
    
    logger.info(f"Comparing schedule against {programs.count()} programs")
    
    for program in programs:
        program_embedding = None
        
        # First try to use the program's direct embedding
        if program.embedding:
            program_embedding = np.array(program.embedding)
        else:
            # If no direct embedding, try to compute from required courses
            required_courses = program.required_courses.all()
            program_course_embeddings = []
            program_weights = []
            
            for course in required_courses:
                if course.embedding:
                    program_course_embeddings.append(course.get_embedding_array())
                    program_weights.append(1.0)  # Could be course.credits
            
            if program_course_embeddings:
                program_embedding = compute_weighted_embedding(program_course_embeddings, program_weights)
        
        if program_embedding is not None:
            # Compute semantic similarity with more variability
            raw_similarity = cosine_similarity(schedule_embedding, program_embedding)
            
            # Apply non-linear transformation to increase variability
            # This will spread out values that are clustered around 0.7
            semantic_similarity = np.tanh(2 * (raw_similarity - 0.5)) * 0.5 + 0.5
            
            final_score = semantic_similarity
            
            # Only include course overlap for CSUSB courses
            if is_csusb:
                schedule_course_codes = set(c.course_code for c in schedule_courses)
                program_course_codes = set(c.course_code for c in program.required_courses.all())
                overlap = len(schedule_course_codes.intersection(program_course_codes)) / len(schedule_course_codes)
                final_score = 0.7 * semantic_similarity + 0.3 * overlap
            
            logger.info(f"Program {program.name}: semantic={semantic_similarity:.3f}, final={final_score:.3f}")
            
            if final_score >= min_similarity:
                similarities.append((program, final_score))
        else:
            logger.warning(f"No embeddings found for program {program.name}")
    
    # Sort by similarity score in descending order
    similarities.sort(key=lambda x: x[1], reverse=True)
    logger.info(f"Found {len(similarities)} programs above similarity threshold {min_similarity}")
    return similarities[:top_n]

def update_schedule_embedding(schedule_id: int) -> None:
    """
    Update a schedule's embedding by computing weighted average of course embeddings.
    """
    schedule = StudentSchedule.objects.get(id=schedule_id)
    course_embeddings = []
    course_weights = []
    
    for course in schedule.courses.all():
        if course.embedding:
            course_embeddings.append(course.get_embedding_array())
            course_weights.append(1.0)  # Could be course.credits
    
    if course_embeddings:
        aggregated = compute_weighted_embedding(course_embeddings, course_weights)
        schedule.embedding = aggregated.tolist()
        schedule.save()

class CourseRecommender:
    def __init__(self):
        self.embeddings = None
        self.course_data = {}
        self.institution_courses = defaultdict(list)
        
    def load_embeddings(self, input_files):
        """Load or generate embeddings for all courses."""
        self.embeddings = generate_course_embeddings(input_files)
        
        # Load course data into memory for quick lookup
        for file in input_files:
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                key = f"{row['institution']}_{row['course_code']}"
                course_data = {
                    'course_code': row['course_code'],
                    'title': row['title'],
                    'description': row['description'],
                    'institution': row['institution']
                }
                self.course_data[key] = course_data
                self.institution_courses[row['institution']].append(key)
    
    def get_course_similarity(self, course_key1, course_key2):
        """Compute cosine similarity between two courses."""
        if course_key1 not in self.embeddings or course_key2 not in self.embeddings:
            return 0.0
        return cosine_similarity(
            np.array(self.embeddings[course_key1]),
            np.array(self.embeddings[course_key2])
        )
    
    def find_similar_courses(self, course_key, n=5, target_institution=None):
        """Find n most similar courses, optionally filtering by institution."""
        if course_key not in self.embeddings:
            return []
            
        # If target institution specified, only compare with courses from that institution
        compare_keys = (
            self.institution_courses[target_institution]
            if target_institution
            else list(self.embeddings.keys())
        )
        
        similarities = []
        source_vec = np.array(self.embeddings[course_key])
        
        for other_key in compare_keys:
            if other_key == course_key:
                continue
                
            sim = self.get_course_similarity(course_key, other_key)
            similarities.append((other_key, sim))
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top n results with course details
        results = []
        for key, sim in similarities[:n]:
            course = self.course_data[key].copy()
            course['similarity_score'] = sim
            results.append(course)
            
        return results
    
    def get_schedule_embedding(self, course_keys):
        """Compute weighted embedding for a schedule of courses."""
        vectors = []
        weights = []
        
        for key in course_keys:
            if key in self.embeddings:
                vectors.append(np.array(self.embeddings[key]))
                weights.append(1.0)  # Could be based on course credits
        
        if vectors:
            return compute_weighted_embedding(vectors, weights)
        return None
    
    def recommend_similar_programs(self, schedule_courses, n=5):
        """Recommend programs based on a student's course schedule."""
        # This is a placeholder - in practice, you would:
        # 1. Load program embeddings (aggregated from their required courses)
        # 2. Compare schedule embedding with program embeddings
        # 3. Return top matches with explanations
        pass
