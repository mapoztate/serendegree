import re
import subprocess
import csv

def extract_text_from_pdf():
    cmd = ['pdftotext', '-raw', 'college-catalog-2022-2023.pdf', '-']
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def clean_text(text):
    # Remove multiple spaces, dots, and numbers at the end
    text = re.sub(r'\.{3,}', ' ', text)
    # Remove unit information from titles
    text = re.sub(r'\s*\d+(?:\.\d+)?\s*units\s*[A-Z]{0,2}\s*$', '', text)
    text = re.sub(r'\s*[0-9.-]+\s*$', '', text)
    # Remove common title artifacts
    text = re.sub(r'\s*total minimum units for the major.*$', '', text)
    text = re.sub(r'\s*Art\s+DIABLO.*$', '', text)
    text = re.sub(r'\s+SC$', '', text)
    text = re.sub(r'Education\s*\d*\s*$', '', text)
    text = re.sub(r'\s*\d+\s*$', '', text)
    text = re.sub(r'S for the Piping Trades.*$', '', text)
    text = re.sub(r'The above courses.*$', '', text)
    # Fix specific word splits while preserving sentence structure
    text = re.sub(r'(\w+)\s+(?=\w+)', r'\1 ', text)
    text = re.sub(r'\s+', ' ', text)
    # Remove trailing periods and spaces
    text = text.strip().rstrip('.')
    return text

def clean_description(text):
    # Remove leading periods, numbers, and spaces
    text = re.sub(r'^[.\s\d]+', '', text)
    # Remove course codes and their descriptions
    text = re.sub(r'[A-Z]{2,4}-[0-9]{3}[^\n.]*', '', text)
    # Clean up C-ID information
    text = re.sub(r'C-ID [A-Z]+ \d+,?\s*', '', text)
    # Remove unit information for cleaning
    text = re.sub(r'\d+(?:\.\d+)?\s*units\s*[A-Z]{1,2}', '', text)
    # Remove lecture/lab hours
    text = re.sub(r'\d+\s*hours\s*(?:lecture|laboratory)\s*per\s*term', '', text)
    # Remove prerequisites and advisories
    text = re.sub(r'(?:Prerequisite|Advisory|Recommended)[^.]*\.', '', text)
    # Remove CSU/UC transfer info
    text = re.sub(r'\s*(?:CSU|UC)[^.]*\.?', '', text)
    # Remove catalog metadata
    text = re.sub(r'DIABLO VALLEY COLLEGE CATALOG[^.]*\.?', '', text)
    text = re.sub(r'PROGRAM/COURSE DESCRIPTIONS[^.]*\.?', '', text)
    text = re.sub(r'chapter four[^.]*\.?', '', text)
    # Remove hyphens and artifacts
    text = re.sub(r'(?:^|\s)-\s*|\s*-(?=\s|$)', ' ', text)
    text = re.sub(r'\s*•.*?(?=\n|$)', '', text)
    
    # Additional word split fixes
    word_splits = {
        'lan guage': 'language',
        'read ing': 'reading',
        'writ ing': 'writing',
        'mate rials': 'materials',
        'docu mentaries': 'documentaries',
        'objec tives': 'objectives',
        'defi nitions': 'definitions',
        'theo ries': 'theories',
        'profes sionals': 'professionals',
        'treat ment': 'treatment',
        'co occurring': 'co-occurring',
        'vari ous': 'various',
        'tech nology': 'technology',
        'tech niques': 'techniques',
        'assess ment': 'assessment',
        'compo nents': 'components',
        'subdivi sions': 'subdivisions',
        'liter ary': 'literary',
        'litera ture': 'literature',
        'ana lyze': 'analyze',
        'ele ments': 'elements',
        'differ ent': 'different',
        'expres sions': 'expressions',
        'instruc tion': 'instruction',
        'socioeco nomic': 'socioeconomic',
        'pre vention': 'prevention',
        'exam ined': 'examined',
        'cohe sion': 'cohesion',
        'communica tion': 'communication',
        'devel opment': 'development',
        'lit erary': 'literary',
        'piec es': 'pieces',
        'set tings': 'settings',
        'learn ing': 'learning',
        'prospec tive': 'prospective',
        'coun try': 'country',
        'cul tural': 'cultural',
        'inter cultural': 'intercultural',
        'objec tives': 'objectives',
        'expres sion': 'expression',
        'direc tion': 'direction',
        'writ ing': 'writing',
        'non fiction': 'non-fiction',
        'intro duction': 'introduction',
        'environ mental': 'environmental',
        'manage ment': 'management',
        'pro gram': 'program',
        'pro gramming': 'programming',
        'soft ware': 'software',
        'data base': 'database',
        'net work': 'network',
        'net working': 'networking',
        'sys tem': 'system',
        'sys tems': 'systems',
        'infor mation': 'information',
        'busi ness': 'business',
        'organ ization': 'organization',
        'organ izational': 'organizational',
        'strat egy': 'strategy',
        'strat egies': 'strategies',
        'admin istration': 'administration',
        'admin istrative': 'administrative'
    }
    
    for split, fixed in word_splits.items():
        text = re.sub(rf'\b{split}\b', fixed, text, flags=re.IGNORECASE)
    
    # Remove incomplete sentences at the end
    text = re.sub(r'\s+(?:and|in|of|the|to|a)\s*$', '', text)
    # Clean up whitespace and punctuation
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*([.,])\s*', r'\1 ', text)
    # Remove any remaining artifacts
    text = re.sub(r'(?:Variable hours|[0-9.-]+\s*$)', '', text)
    text = re.sub(r'(?:defi|pro)\s*$', '', text)
    
    # Remove program/catalog information more aggressively
    program_patterns = [
        r'(?:The associate in|Students completing|To earn|This program|This course is designed for students who)[^.]*\.',
        r'(?:major requirements:|required courses:|total minimum units|certificate requirements)[^.]*\.?',
        r'(?:Students must complete|Students transferring|This degree may not)[^.]*\.?',
        r'(?:Some courses in the major|Some variations in requirements)[^.]*\.?',
        r'(?:Certificate of accomplishment|Certificate of achievement)[^.]*\.?',
        r'(?:All required courses|All coursework|This curriculum)[^.]*\.?',
        r'(?:The above courses|See course description)[^.]*\.?',
        r'(?:The DVC|The program|The major|The certificate)[^.]*\.?',
        r'(?:All coursework|This curriculum)[^.]*\.?'
    ]
    
    for pattern in program_patterns:
        text = re.sub(pattern, '', text)
    
    # Improve sentence structure
    text = re.sub(r'This course is equivalent to two years of high school study\.?', '', text)
    text = re.sub(r'This course is (?:conducted|taught) entirely in (?:Spanish|Russian)\.?', '', text)
    text = re.sub(r'This course does not satisfy [^.]+\.?', '', text)
    text = re.sub(r'This course presents an overview of', 'An overview of', text)
    text = re.sub(r'This course provides an overview of', 'An overview of', text)
    text = re.sub(r'This course introduces', 'Introduces', text)
    text = re.sub(r'This course covers', 'Covers', text)
    text = re.sub(r'This course explores', 'Explores', text)
    text = re.sub(r'This course examines', 'Examines', text)
    text = re.sub(r'This course focuses', 'Focuses', text)
    text = re.sub(r'This course emphasizes', 'Emphasizes', text)
    
    # Final cleanup
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    # Remove any trailing units text that wasn't caught earlier
    text = re.sub(r'\s*\d+\s*units\s*[A-Z]{0,2}\s*$', '', text)
    
    # Remove any remaining incomplete descriptions
    if len(text) < 30 and ('units' in text.lower() or text.startswith('taught entirely')):
        return 'Course description not available'
        
    return text

def is_valid_description(text):
    # Filter out program-level information and other non-course descriptions
    invalid_starts = [
        'students completing the program',
        'students may not',
        'certificate of achievement',
        'certificate of accomplishment',
        'associate in',
        'major requirements',
        'required courses',
        'total minimum',
        'possible career',
        'department and instruction office',
        'diablo valley college catalog',
        'program/course descriptions',
        'chapter four',
        'the program requires',
        'the certificate requires',
        'the major requires',
        'students must complete',
        'students transferring',
        'this degree may not',
        'all coursework',
        'this curriculum',
        'all required courses',
        'the above courses'
    ]
    text_lower = text.lower()
    return not any(text_lower.startswith(start) for start in invalid_starts)

def extract_description(context):
    # Try to find a proper course description
    desc_patterns = [
        r'This course[^.]+(?:\.[^.]+)*\.',
        r'An introduction[^.]+(?:\.[^.]+)*\.',
        r'A study[^.]+(?:\.[^.]+)*\.',
        r'Topics include[^.]+(?:\.[^.]+)*\.',
        r'Students will[^.]+(?:\.[^.]+)*\.',
        r'Designed to[^.]+(?:\.[^.]+)*\.',
        r'Focuses on[^.]+(?:\.[^.]+)*\.',
        r'Emphasizes[^.]+(?:\.[^.]+)*\.',
        r'Explores[^.]+(?:\.[^.]+)*\.',
        r'Examines[^.]+(?:\.[^.]+)*\.',
        r'Covers[^.]+(?:\.[^.]+)*\.',
        r'[A-Z][^.]+(?:\.[^.]+)*\.'  # Any sentence starting with capital letter
    ]
    
    # Try to find the best description
    best_desc = ''
    for pattern in desc_patterns:
        matches = re.finditer(pattern, context)
        for match in matches:
            desc = match.group(0)
            if is_valid_description(desc) and len(desc) <= 1000:  # Limit description length
                # If we find a longer valid description, use it
                if len(desc) > len(best_desc):
                    best_desc = desc
    
    return best_desc

def natural_sort_key(course_code):
    """Create a key for natural sorting of course codes."""
    prefix, number = course_code.split('-')
    return (prefix, int(number))

def standardize_title_case(title):
    """Properly capitalize course titles according to academic standards."""
    # Words that should not be capitalized unless at the start
    lowercase_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 
                      'of', 'on', 'or', 'the', 'to', 'with'}
    
    words = title.split()
    if not words:
        return title
        
    # Capitalize first word always
    result = [words[0].capitalize()]
    
    # Process remaining words
    for word in words[1:]:
        if word.lower() in lowercase_words:
            result.append(word.lower())
        else:
            # Keep existing capitalization for abbreviations
            if word.isupper() and len(word) <= 4:
                result.append(word)
            else:
                result.append(word.capitalize())
    
    return ' '.join(result)

def validate_course_code(code):
    """
    Validate and clean course codes to ensure they follow the standard format.
    Returns cleaned code if valid, None if invalid.
    """
    # Remove any whitespace
    code = code.strip()
    
    # Basic format check: 2-4 letters, hyphen, 3 digits
    pattern = re.compile(r'^[A-Z]{2,4}-\d{3}$')
    if not pattern.match(code):
        return None
        
    # Known department prefixes (add more as needed)
    valid_prefixes = {
        'ADJUS', 'ANTHR', 'ARCHI', 'ART', 'ARTDM', 'ASTRO', 'BCA', 'BIOSC',
        'BUS', 'BUSMG', 'BUSAC', 'CHEM', 'CHIN', 'COMM', 'COMSC', 'CONST',
        'COOP', 'CULN', 'DANCE', 'DRAMA', 'ECE', 'ECON', 'EDUC', 'ENGL',
        'ENGIN', 'ESL', 'FILM', 'FRNCH', 'GEOG', 'GEOL', 'GRMAN', 'HIST',
        'HSCI', 'HUMAN', 'ITAL', 'JAPAN', 'JRNAL', 'KINES', 'LS', 'MATH',
        'MUSIC', 'NUTRI', 'OCEAN', 'PE', 'PEDAN', 'PHIL', 'PHYS', 'POLSC',
        'PSYCH', 'RE', 'RUSS', 'SIGN', 'SOCIO', 'SPAN', 'SPCH'
    }
    
    prefix = code.split('-')[0]
    if prefix not in valid_prefixes:
        return None
        
    return code

def parse_course_info(text):
    courses = []
    
    # Regular expressions for course information
    course_pattern = re.compile(r'^([A-Z]{2,4}-[0-9]{3})\s+(.+?)(?=\s{2,}|\n|$)')
    units_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*units')
    
    lines = text.split('\n')
    current_course = None
    current_context = []
    
    for i, line in enumerate(lines):
        course_match = course_pattern.match(line)
        if course_match:
            # Process previous course if exists
            if current_course:
                # Look for description in accumulated context
                context = '\n'.join(current_context)
                
                # If title is short or ends with 'and', try to extend it from context
                if len(current_course['title']) < 20 or current_course['title'].strip().endswith('and'):
                    next_line = current_context[1] if len(current_context) > 1 else ''
                    if not course_pattern.match(next_line):
                        # Find the first sentence or up to the first period
                        title_extension = re.match(r'^([^.]+)', next_line)
                        if title_extension:
                            current_course['title'] = clean_text(current_course['title'] + ' ' + title_extension.group(1))
                
                # Clean up title
                current_course['title'] = re.sub(r'\s*Art\s+DIABLO.*$', '', current_course['title'])
                current_course['title'] = re.sub(r'\s+SC$', '', current_course['title'])
                current_course['title'] = re.sub(r'Education\s*\d*\s*$', '', current_course['title'])
                current_course['title'] = re.sub(r'\s*\d+\s*$', '', current_course['title'])
                current_course['title'] = re.sub(r'S for the Piping Trades.*$', '', current_course['title'])
                current_course['title'] = re.sub(r'The above courses.*$', '', current_course['title'])
                current_course['title'] = re.sub(r'\s+and\s*$', '', current_course['title'])
                
                # Standardize title case
                current_course['title'] = standardize_title_case(current_course['title'])
                
                description = extract_description(context)
                units_match = units_pattern.search(context)
                units = units_match.group(1) if units_match else ''
                
                if description:
                    full_desc = clean_description(description)
                    if units and not re.search(r'\(\d+(?:\.\d+)?\s*units\)', full_desc):
                        full_desc += f" ({units} units)"
                else:
                    full_desc = f"({units} units)" if units else "Course description not available"
                
                # Only add if we have meaningful information
                if len(current_course['title']) > 3 and (len(full_desc) > 30 or full_desc == "Course description not available"):
                    current_course['description'] = full_desc
                    courses.append(current_course)
            
            # Start new course
            course_code = course_match.group(1)
            # Validate course code
            cleaned_code = validate_course_code(course_code)
            if cleaned_code:
                current_course = {
                    'course_code': cleaned_code,
                    'title': clean_text(course_match.group(2)),
                    'institution': 'Diablo Valley College'
                }
                current_context = [line]
            else:
                current_course = None
                current_context = []
        elif current_course:
            current_context.append(line)
    
    # Process the last course
    if current_course:
        context = '\n'.join(current_context)
        
        # If title is short or ends with 'and', try to extend it from context
        if len(current_course['title']) < 20 or current_course['title'].strip().endswith('and'):
            next_line = current_context[1] if len(current_context) > 1 else ''
            if not course_pattern.match(next_line):
                # Find the first sentence or up to the first period
                title_extension = re.match(r'^([^.]+)', next_line)
                if title_extension:
                    current_course['title'] = clean_text(current_course['title'] + ' ' + title_extension.group(1))
        
        # Clean up title
        current_course['title'] = re.sub(r'\s*Art\s+DIABLO.*$', '', current_course['title'])
        current_course['title'] = re.sub(r'\s+SC$', '', current_course['title'])
        current_course['title'] = re.sub(r'Education\s*\d*\s*$', '', current_course['title'])
        current_course['title'] = re.sub(r'\s*\d+\s*$', '', current_course['title'])
        current_course['title'] = re.sub(r'S for the Piping Trades.*$', '', current_course['title'])
        current_course['title'] = re.sub(r'The above courses.*$', '', current_course['title'])
        current_course['title'] = re.sub(r'\s+and\s*$', '', current_course['title'])
        
        # Standardize title case
        current_course['title'] = standardize_title_case(current_course['title'])
        
        description = extract_description(context)
        units_match = units_pattern.search(context)
        units = units_match.group(1) if units_match else ''
        
        if description:
            full_desc = clean_description(description)
            if units and not re.search(r'\(\d+(?:\.\d+)?\s*units\)', full_desc):
                full_desc += f" ({units} units)"
        else:
            full_desc = f"({units} units)" if units else "Course description not available"
        
        if len(current_course['title']) > 3 and (len(full_desc) > 30 or full_desc == "Course description not available"):
            current_course['description'] = full_desc
            courses.append(current_course)
    
    # Sort courses using natural sort
    courses.sort(key=lambda x: natural_sort_key(x['course_code']))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_courses = []
    for course in courses:
        if course['course_code'] not in seen:
            seen.add(course['course_code'])
            unique_courses.append(course)
    
    return unique_courses

def write_courses_csv(courses):
    with open('sample_courses.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['course_code', 'title', 'description', 'institution'], 
                              quoting=csv.QUOTE_ALL)  # Quote all fields
        writer.writeheader()
        for course in courses:
            # Clean up any remaining newlines in fields
            cleaned_course = {
                k: v.replace('\n', ' ').strip() if isinstance(v, str) else v 
                for k, v in course.items()
            }
            writer.writerow(cleaned_course)

def main():
    text = extract_text_from_pdf()
    courses = parse_course_info(text)
    write_courses_csv(courses)
    print(f"Processed {len(courses)} unique courses")

if __name__ == '__main__':
    main() 