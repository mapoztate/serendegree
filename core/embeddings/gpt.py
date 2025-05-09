import os
from typing import List, Dict
from openai import OpenAI
from ..models import Program, Course

def get_openai_client():
    """Get OpenAI client with API key from environment."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)

def generate_program_explanation(
    program: Program,
    student_courses: List[Course],
    similarity_score: float
) -> str:
    """
    Generate a student-friendly explanation of why a program matches their courses.
    
    Args:
        program: The matched Program instance
        student_courses: List of Course instances the student has taken
        similarity_score: Cosine similarity score between program and student schedule
    
    Returns:
        A natural language explanation of the match
    """
    # Format course information
    student_course_info = "\n".join([
        f"- {course.course_code}: {course.title}"
        for course in student_courses
    ])
    
    program_course_info = "\n".join([
        f"- {course.course_code}: {course.title}"
        for course in program.required_courses.all()
    ])
    
    # Construct the prompt
    prompt = f"""As an academic advisor, explain why the {program.name} program at {program.institution} 
(similarity score: {similarity_score:.2f}) would be a good fit for a student who has taken these courses:

Student's Completed Courses:
{student_course_info}

Program Required Courses:
{program_course_info}

Program Description:
{program.description}

Please provide a concise, encouraging explanation focusing on:
1. How their completed courses align with the program
2. What skills they've likely developed that would be valuable
3. Potential career paths this program could lead to
"""

    # Call GPT-4 API
    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a knowledgeable and encouraging academic advisor helping students find their ideal major."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content

def generate_batch_explanations(
    matches: List[Dict],
    student_courses: List[Course]
) -> List[Dict]:
    """
    Generate explanations for multiple program matches.
    
    Args:
        matches: List of dicts containing program and similarity score
        student_courses: List of Course instances the student has taken
    
    Returns:
        List of dicts with programs, scores, and explanations
    """
    results = []
    for match in matches:
        program = match['program']
        similarity = match['similarity']
        
        explanation = generate_program_explanation(
            program,
            student_courses,
            similarity
        )
        
        results.append({
            'program': program,
            'similarity': similarity,
            'explanation': explanation
        })
    
    return results
