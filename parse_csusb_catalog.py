import pdfplumber
import csv
import re

def clean_text(text):
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove any text in parentheses
    text = re.sub(r'\([^)]*\)', '', text)
    return text.strip()

def extract_courses_from_pdf(pdf_path):
    courses = []
    seen_courses = set()  # To avoid duplicates
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            text = clean_text(text)
            
            # Pattern to match course code, title, and units
            # Looking for patterns like "HSCI 3051 Health and Human Ecology 3"
            # Ensuring units are between 1-6 and title doesn't contain numbers
            pattern = r'([A-Z]{2,4})\s+(\d{3,4}[A-Z]?)\s+([^0-9\n]{3,}?)\s+([1-6])(?:\s|$)'
            
            matches = re.finditer(pattern, text)
            
            for match in matches:
                dept = match.group(1).strip()
                number = match.group(2).strip()
                course_code = f"{dept} {number}"
                title = match.group(3).strip()
                units = match.group(4)
                
                # Skip if we've seen this course before
                if course_code in seen_courses:
                    continue
                    
                # Skip if title looks suspicious
                if len(title) < 3 or "choose" in title.lower() or "units from" in title.lower():
                    continue
                
                # Create description by combining title and units
                description = f"{title} ({units} units)"
                
                courses.append({
                    'course_code': course_code,
                    'title': title,
                    'description': description,
                    'institution': 'California State University, San Bernardino'
                })
                seen_courses.add(course_code)
    
    return courses

def save_to_csv(courses, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['course_code', 'title', 'description', 'institution'])
        writer.writeheader()
        writer.writerows(courses)

if __name__ == "__main__":
    pdf_path = "2022-23.pdf"
    output_file = "csusb_courses.csv"
    
    try:
        courses = extract_courses_from_pdf(pdf_path)
        save_to_csv(courses, output_file)
        print(f"Successfully extracted {len(courses)} courses to {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}") 