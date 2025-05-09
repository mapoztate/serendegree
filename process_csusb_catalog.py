import re
import subprocess
import csv
import logging
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_text_from_pdf():
    """Extract text from the CSUSB PDF catalog."""
    cmd = ['pdftotext', '-raw', '2022-23.pdf', '-']
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def find_course_section(text: str) -> str:
    """Find the section of the PDF containing course listings."""
    # Look for sections that contain multiple course patterns
    course_pattern = re.compile(
        r'([A-Z]{2,4}\s+\d{3,4}[A-Z]?\..*?Units:\s*\d+)',
        re.MULTILINE | re.DOTALL
    )
    
    # Split text into chunks and look for sections with course patterns
    chunks = text.split('\n\n')
    course_sections = []
    
    for i, chunk in enumerate(chunks):
        matches = list(course_pattern.finditer(chunk))
        if len(matches) > 2:  # If chunk has multiple course patterns
            course_sections.append(chunk)
            logging.info(f"Found course section with {len(matches)} courses")
            # Get some sample courses
            for match in matches[:3]:
                logging.info(f"Sample course: {match.group(1)}")
    
    if course_sections:
        return '\n\n'.join(course_sections)
    return text

def clean_course_code(code: str) -> str:
    """Clean and standardize course codes."""
    code = code.strip().upper()
    code = re.sub(r'(\d+)', r' \1', code)
    code = re.sub(r'\s+', ' ', code)
    return code

def clean_title(title: str) -> str:
    """Clean and standardize course titles."""
    # Remove common artifacts
    title = re.sub(r'\s*\([^)]*\)\s*$', '', title)  # Remove parenthetical notes
    title = re.sub(r'\s*\d+\s*units?\s*$', '', title)  # Remove unit information
    title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
    title = re.sub(r'[Ss]emester\s+[Pp]rerequisite:.*$', '', title)
    title = re.sub(r'[Qq]uarter\s+[Pp]rerequisite:.*$', '', title)
    title = re.sub(r'Offered as.*$', '', title)  # Remove cross-listing info
    
    # Expand common abbreviations
    title = re.sub(r'\bIntro\b', 'Introduction', title)
    title = re.sub(r'\bAdv\b', 'Advanced', title)
    title = re.sub(r'\bLab\b', 'Laboratory', title)
    title = re.sub(r'\bComp\b', 'Computer', title)
    title = re.sub(r'\bSys\b', 'Systems', title)
    title = re.sub(r'\bMgt\b', 'Management', title)
    title = re.sub(r'\bOrg\b', 'Organization', title)
    title = re.sub(r'\bTech\b', 'Technology', title)
    title = re.sub(r'\bProg\b', 'Programming', title)
    title = re.sub(r'\bAdmin\b', 'Administration', title)
    title = re.sub(r'\bBus\b', 'Business', title)
    title = re.sub(r'\bEcon\b', 'Economics', title)
    title = re.sub(r'\bEd\b', 'Education', title)
    title = re.sub(r'\bPsych\b', 'Psychology', title)
    
    return title.strip()

def clean_description(desc: str) -> str:
    """Clean and standardize course descriptions."""
    if not desc:
        return ""
    
    # First, extract only the description part (before any subsequent course info)
    desc = re.split(r'\s+(?=[A-Z]{2,4}\s+\d{3,4}[A-Z]?\.)', desc)[0]
    
    # Remove common artifacts
    cleaners = [
        (r'Prerequisites?:[^.]+\.', ''),
        (r'Corequisites?:[^.]+\.', ''),
        (r'Formerly[^.]+\.', ''),
        (r'Quarter units?:[^.]+\.', ''),
        (r'Graded [A-Za-z/-]+\.', ''),
        (r'Semester Prerequisite:[^.]+\.', ''),
        (r'Quarter Prerequisite:[^.]+\.', ''),
        (r'Materials fee required\.', ''),
        (r'(?:Previously|Formerly) (?:known as|offered as)[^.]+\.', ''),
        (r'May be (?:taken|repeated)[^.]+\.', ''),
        (r'A total of [^.]+\.', ''),
        (r'Satisfies [^.]+\.', ''),
        (r'\b[A-Z]{2,4}\s+\d{3,4}[A-Z]?\b', ''),  # Remove course codes
        (r'\n+', ' '),  # Replace newlines
        (r'\s+', ' '),  # Normalize whitespace
        (r'^\s*\.\s*', ''),  # Remove leading periods
        (r'\s*\.\s*$', '.'),  # Clean up trailing periods
        (r'(?<=[.!?])\s+[^.!?]*$', ''),  # Remove incomplete sentences
        (r'Units?:\s*\d+\s*\.', ''),  # Remove unit information
        (r'Offered as[^.]+\.', ''),  # Remove cross-listing info
        (r'students may not receive credit for both\.', ''),  # Remove credit restriction
        (r'\([^)]*\)', '')  # Remove parenthetical notes
    ]
    
    for pattern, replacement in cleaners:
        desc = re.sub(pattern, replacement, desc)
    
    desc = desc.strip()
    if not desc.endswith('.'):
        desc += '.'
        
    return desc

def should_skip_course(code: str, title: str, desc: str) -> bool:
    """Enhanced course filtering."""
    skip_patterns = [
        r'independent.*(?:study|research)',
        r'internship',
        r'thesis',
        r'dissertation',
        r'special.*topics',
        r'directed.*(?:study|research)',
        r'continuous enrollment',
        r'selected topics',
        r'seminar in',
        r'individual.*study',
        r'supervised.*(?:study|research)',
        r'graduate.*research',
        r'masters.*(?:thesis|project)',
        r'doctoral.*dissertation',
        r'practicum',
        r'field.*work',
        r'comprehensive.*examination',
        r'culminating.*experience',
        r'independent.*project',
        r'portfolio',
        r'comprehensive.*assessment',
        r'continuous.*registration',
        r'graduate.*project',
        r'graduate.*thesis',
        r'graduate.*comprehensive.*examination',
        r'graduate.*portfolio',
        r'graduate.*assessment'
    ]
    
    text_to_check = f"{title} {desc}".lower()
    
    if any(re.search(pattern, text_to_check) for pattern in skip_patterns):
        return True
        
    if len(desc) < 50:  # Increased minimum length
        return True
        
    # Skip generic descriptions
    generic_patterns = [
        r'^individual study\.',
        r'^special topics\.',
        r'^selected topics\.',
        r'^independent research\.',
        r'^examination\.',
        r'^continuation of\.',
        r'^see department\.',
        r'^topics vary\.',
        r'^consent of instructor required\.',
        r'^consent of department required\.'
    ]
    if any(re.search(pattern, desc.lower()) for pattern in generic_patterns):
        return True
        
    return False

def validate_course(course: Dict[str, str]) -> bool:
    """Validate course data."""
    # Check for required fields
    if not all(course.get(field) for field in ['course_code', 'title', 'description']):
        return False
        
    # Check for minimum lengths
    if len(course['title']) < 3:
        return False
    if len(course['description']) < 50:
        return False
        
    # Check for invalid characters or patterns
    if re.search(r'[^\w\s.,;:()\-\'"/&]+', course['title']):
        return False
    if re.search(r'[^\w\s.,;:()\-\'"/&]+', course['description']):
        return False
        
    # Check for reasonable lengths
    if len(course['title']) > 200:
        return False
    if len(course['description']) > 2000:
        return False
        
    return True

def extract_course_info(text: str) -> List[Dict[str, str]]:
    """Extract course information from the catalog text."""
    courses = []
    
    # Pattern to match course entries
    course_pattern = re.compile(
        r'([A-Z]{2,4})\s+(\d{3,4}[A-Z]?)\.\s+'  # Course code
        r'([^.]+?)\.\s+'  # Title
        r'(?:Units?:\s*)?(\d+)\s*\.\s*'  # Units
        r'([^.]+(?:\.[^.]+)*\.)'  # Description (multiple sentences)
        r'(?=\s*[A-Z]{2,4}\s+\d{3,4}[A-Z]?\.|\s*$)',  # Look ahead for next course or end
        re.MULTILINE | re.DOTALL
    )
    
    # Find all course matches
    matches = list(course_pattern.finditer(text))
    logging.info(f"Found {len(matches)} potential course matches")
    
    for i, match in enumerate(matches):
        try:
            dept, num, title, units, desc = match.groups()
            
            # Clean and format the data
            course_code = clean_course_code(f"{dept} {num}")
            title = clean_title(title)
            description = clean_description(desc)
            
            # Skip invalid or unwanted courses
            if not description or should_skip_course(course_code, title, description):
                continue
            
            # Create course entry
            course = {
                'course_code': course_code,
                'title': title,
                'description': f"{description} ({units} units)",
                'institution': 'California State University, San Bernardino'
            }
            
            if not validate_course(course):
                continue
                
            courses.append(course)
            
            # Log sample courses for debugging
            if len(courses) <= 5 or len(courses) >= len(matches) - 5:
                logging.info(f"Course {len(courses)}: {course['course_code']} - {course['title']}")
                
        except Exception as e:
            logging.error(f"Error processing match {i+1}: {str(e)}")
            logging.error(f"Match text: {match.group(0)[:200]}...")
    
    # Sort and deduplicate courses
    courses.sort(key=lambda x: x['course_code'])
    seen = set()
    unique_courses = []
    for course in courses:
        if course['course_code'] not in seen:
            seen.add(course['course_code'])
            unique_courses.append(course)
    
    return unique_courses

def write_courses_csv(courses: List[Dict[str, str]], filename: str = 'csusb_courses.csv'):
    """Write courses to CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, 
                              fieldnames=['course_code', 'title', 'description', 'institution'],
                              quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for course in courses:
            writer.writerow(course)

def process_statistics(courses: List[Dict[str, str]]):
    """Generate processing statistics."""
    stats = {
        'total_courses': len(courses),
        'courses_by_department': {},
        'avg_description_length': sum(len(c['description']) for c in courses) / max(len(courses), 1),
    }
    
    for course in courses:
        dept = course['course_code'].split()[0]
        stats['courses_by_department'][dept] = stats['courses_by_department'].get(dept, 0) + 1
    
    logging.info("Processing Statistics:")
    for key, value in stats.items():
        if isinstance(value, dict):
            logging.info(f"{key}:")
            for k, v in value.items():
                logging.info(f"  {k}: {v}")
        else:
            logging.info(f"{key}: {value}")

def main():
    logging.info("Starting CSUSB catalog processing")
    
    text = extract_text_from_pdf()
    logging.info("PDF text extracted successfully")
    
    courses = extract_course_info(text)
    logging.info(f"Extracted {len(courses)} courses")
    
    write_courses_csv(courses)
    process_statistics(courses)
    
    logging.info("Processing complete")

if __name__ == '__main__':
    main() 