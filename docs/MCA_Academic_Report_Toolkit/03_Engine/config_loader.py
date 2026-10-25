import os
import json

def get_config_path():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_dir, "01_Inputs", "config.json")

def load_student_config():
    """Loads configuration from 01_Inputs/config.json with safe academic defaults."""
    cfg_path = get_config_path()
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to read {cfg_path}: {e}")

    # Generic fallback default dictionary
    return {
        "institution": {
            "college_name": "AMAL JYOTHI COLLEGE OF ENGINEERING AUTONOMOUS",
            "location": "KANJIRAPPALLY, KOORALI P.O., KOTTAYAM, KERALA - 686507",
            "department": "DEPARTMENT OF COMPUTER APPLICATIONS",
            "degree": "Master of Computer Applications",
            "academic_year": "2025–2027",
            "course_code": "24MCAR295",
            "course_title": "RESEARCH PROJECT / SOFTWARE PROJECT PART 1"
        },
        "student": {
            "full_name": "STUDENT FULL NAME",
            "reg_number": "AJC25MCA-XXXX",
            "roll_number": "XX",
            "class_section": "RMCA 2025-27 S3",
            "email": "student@mca.ajce.in"
        },
        "faculty": {
            "project_guide_name": "PROJECT GUIDE NAME",
            "project_guide_designation": "Assistant Professor",
            "hod_name": "Dr. Juby Mathew",
            "hod_designation": "Professor & Head of Department",
            "scrum_master": "PROJECT GUIDE NAME"
        },
        "project": {
            "title": "ENTER YOUR PROJECT TITLE HERE",
            "short_name": "PROJECT",
            "tagline": "A Concise Subtitle Describing Your System Architecture",
            "category": "Application Development & Cloud Computing",
            "target_platform": "Target Operating System / Web / Mobile Platform",
            "primary_language": "Programming Language & UI Framework",
            "backend_infrastructure": "Backend Server, Database & Cloud Infrastructure",
            "geospatial_engine": "Geospatial / Navigation Services (if applicable)",
            "payment_gateway": "Payment Gateway API (if applicable)",
            "background_hud": "System Background Services (if applicable)"
        },
        "field_investigation": {
            "organization_name": "FIELD STUDY ENTERPRISE / ORGANIZATION NAME",
            "business_nature": "Nature of Business Operations & Services",
            "establishment_type": "Enterprise Classification / SME / Corporate",
            "location": "City, District, State",
            "key_informant": "Key Informant Designation / Business Owner",
            "geotagged_photos": []
        },
        "evaluation_metrics": {
            "sus_score": 85.0,
            "sus_grade": "Grade A Excellent",
            "test_users_count": 30,
            "firestore_latency_ms": 200,
            "anr_incidents": 0,
            "memory_mb": 120
        }
    }
