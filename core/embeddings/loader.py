import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from django.db import transaction
from ..models import Course, Program

def load_course_embeddings(file_path: str) -> Dict[str, np.ndarray]:
    """
    Load course embeddings from a CSV file.
    Expected format: course_code,embedding (where embedding is a comma-separated list of floats)
    """
    df = pd.read_csv(file_path)
    embeddings = {}
    
    for _, row in df.iterrows():
        course_code = row['course_code']
        embedding = np.array([float(x) for x in row['embedding'].split(',')])
        embeddings[course_code] = embedding
    
    return embeddings

@transaction.atomic
def update_course_embeddings(embeddings: Dict[str, np.ndarray]) -> None:
    """Update course embeddings in the database."""
    for course_code, embedding in embeddings.items():
        Course.objects.filter(course_code=course_code).update(
            embedding=embedding.tolist()
        )

def aggregate_embeddings(embeddings: List[np.ndarray]) -> np.ndarray:
    """
    Aggregate multiple embeddings into a single vector by taking their mean.
    """
    if not embeddings:
        return None
    return np.mean(embeddings, axis=0)

@transaction.atomic
def update_program_embeddings(program_id: int) -> None:
    """
    Update program embedding by aggregating its required courses' embeddings.
    """
    program = Program.objects.get(id=program_id)
    course_embeddings = [
        course.get_embedding_array()
        for course in program.required_courses.all()
        if course.embedding is not None
    ]
    
    if course_embeddings:
        aggregated = aggregate_embeddings(course_embeddings)
        program.embedding = aggregated.tolist()
        program.save()

def load_embeddings_from_csv(file_path: str, batch_size: int = 1000) -> None:
    """
    Load and process embeddings from a CSV file in batches.
    """
    embeddings = load_course_embeddings(file_path)
    
    # Process in batches to avoid memory issues
    course_codes = list(embeddings.keys())
    for i in range(0, len(course_codes), batch_size):
        batch_codes = course_codes[i:i + batch_size]
        batch_embeddings = {
            code: embeddings[code] for code in batch_codes
        }
        update_course_embeddings(batch_embeddings)
