import numpy as np
from typing import List
from ..models import Course, Program
from .course_embeddings import train_word2vec_model, get_document_embedding
import pandas as pd

def update_course_embeddings():
    """Update all course embeddings using Word2Vec."""
    # Prepare DataFrame for Word2Vec training
    courses = Course.objects.all()
    programs = Program.objects.all()
    
    # Combine course and program data for better context
    training_data = []
    
    # Add course data
    for course in courses:
        training_data.append({
            'title': course.title,
            'description': course.description,
            'code': course.course_code,
            'type': 'course',
            'institution': 'CSUSB'
        })
    
    # Add program data
    for program in programs:
        training_data.append({
            'title': program.name,
            'description': program.description or '',  # Handle None
            'code': '',  # Programs don't have codes
            'type': 'program',
            'institution': 'CSUSB'
        })
    
    training_df = pd.DataFrame(training_data)
    
    # Train Word2Vec model on all data
    model = train_word2vec_model(training_df)
    
    # Generate and save course embeddings
    for course in courses:
        text = f"{course.course_code} {course.title} {course.description}"
        embedding = get_document_embedding(text, model)
        if embedding is not None:  # Check for valid embedding
            course.embedding = embedding.tolist()
            course.save()
    
    return model  # Return model for reuse in program embeddings

def update_program_embeddings():
    """Update all program embeddings using either description, courses, or both."""
    # First get the Word2Vec model from course training
    model = update_course_embeddings()
    
    for program in Program.objects.all():
        embeddings_to_combine = []
        
        # Try to get course-based embedding
        course_embeddings = [
            course.get_embedding_array()
            for course in program.required_courses.all()
            if course.embedding is not None
        ]
        if course_embeddings:
            course_embedding = np.mean(course_embeddings, axis=0)
            embeddings_to_combine.append(course_embedding)
        
        # Try to get description-based embedding
        if program.name or program.description:
            text = f"{program.name} {program.description or ''}"
            desc_embedding = get_document_embedding(text, model)
            if desc_embedding is not None:
                embeddings_to_combine.append(desc_embedding)
        
        # If we have any embeddings to combine
        if embeddings_to_combine:
            # Average all available embeddings
            program_embedding = np.mean(embeddings_to_combine, axis=0)
            # Normalize
            program_embedding = program_embedding / np.linalg.norm(program_embedding)
            program.embedding = program_embedding.tolist()
            program.save() 