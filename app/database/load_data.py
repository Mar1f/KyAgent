import os
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
import glob
import logging
import sys

# --- Correctly add project root to sys.path --- 
# Calculate the project root directory (two levels up from app/database)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root) # Use insert(0, ...) to prioritize project root
# --- End Path Correction --- 

from dotenv import load_dotenv

dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

try:
    from app_config import DATABASE_URL, DB_ENV_VARS, validate_required_env
    # Import updated models
    # Now that project root is in path, we might need to adjust this import if models.py also needs root access
    # Let's keep it as is for now, assuming models.py can find app_config.py
    from app.database.models import Base, School, Program, SessionLocal
except ImportError as e:
    print(f"Error importing config or models: {e}")
    print(f"Ensure app_config.py exists at {project_root} and models.py is in app/database.")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Discipline Category Mapping (Based on first 2 digits of program_code) ---
# Verify these codes against official standards if possible
DISCIPLINE_CODE_MAP = {
    "01": "哲学",
    "02": "经济学",
    "03": "法学",
    "04": "教育学",
    "05": "文学",
    "06": "历史学",
    "07": "理学",
    "08": "工学",
    "09": "农学",
    "10": "医学",
    "11": "军事学",
    "12": "管理学",
    "13": "艺术学",
    # Add any other specific codes if necessary
}
DEFAULT_DISCIPLINE_CATEGORY = "其他" # Default if code doesn't match

# --- Column Name Mappings (ADJUST THESE BASED ON YOUR EXCEL FILES) ---
# These *must* match your actual Excel column headers for SCHOOL data.
COL_MAP_SCHOOL = {
    # Excel Header        : Database Column Name (from models.py)
    '学校'            : 'name',
    '学校省份'            : 'province',
    '学校属性'            : 'type', # Mapping to 'type' column in your schema
    '学校官网'            : 'website',
    '学校研究生官网'      : 'grad_website',
    '学校电话'            : 'phone',
    '学校邮箱'            : 'email',
    '学校地址'            : 'address',
    '隶属'                : 'affiliation',
    '硕士点'              : 'master_programs',
    '博士点'              : 'doctoral_programs',
    '国家重点学科'        : 'key_disciplines', # Assuming this Excel col contains counts
    '重点实验室'          : 'key_labs'
}

# These *must* match your actual Excel column headers for PROGRAM/SCORE data.
COL_MAP_PROGRAM = {
    # Excel Header        : Database Column Name (from models.py)
    '学校'                : 'school_name',
    '年份'                : 'year',
    '硕士类型'            : 'program_type', # Mapping '硕士类型' Excel column
    '专业代码'            : 'program_code',
    '专业名称'            : 'program_name',
    '总分'                : 'total_score',
    '政治'                : 'politics_score',
    '英语'                : 'english_score',
    '专业课一'            : 'major_score1',
    '专业课二'            : 'major_score2',
    '备注'                : 'notes'
}
# --- End Column Name Mappings ---

def get_or_create_school(session, school_data):
    """Gets a school by name or creates it if it doesn't exist."""
    name = school_data.get('name')
    if not name:
        logging.warning("Skipping entry with missing school name.")
        return None

    # Use updated model name School
    school = session.query(School).filter_by(name=name).first()
    if school:
        # Optionally update existing school data here if needed
        # logging.info(f"Found existing school: {name}")
        pass
    else:
        # Use updated model name School
        school = School(**school_data)
        session.add(school)
        try:
            session.flush() # Flush to get the ID
            logging.info(f"Created new school: {name}")
        except IntegrityError:
            session.rollback()
            logging.error(f"Integrity error creating school: {name}. It might already exist.")
            school = session.query(School).filter_by(name=name).first()
        except Exception as e:
            session.rollback()
            logging.error(f"Error creating school {name}: {e}")
            return None
    return school

def update_program_from_data(program, program_data):
    """Update a Program ORM object with the latest imported values."""
    for field, value in program_data.items():
        setattr(program, field, value)


def find_existing_program(session, school_id, program_data):
    """Find an existing program row for idempotent imports."""
    year = program_data.get('year')
    if not school_id or not year:
        return None

    program_code = program_data.get('program_code')
    program_name = program_data.get('program_name')
    program_type = program_data.get('program_type')

    query = session.query(Program).filter(
        Program.school_id == school_id,
        Program.year == year
    )

    normalized_code = str(program_code).strip() if program_code is not None else None
    if normalized_code:
        existing = query.filter(Program.program_code == normalized_code).first()
        if existing:
            return existing

    if program_name:
        fallback_query = query.filter(Program.program_name == program_name)
        if program_type:
            fallback_query = fallback_query.filter(Program.program_type == program_type)
        return fallback_query.first()

    return None


def load_excel_data(session, file_path):
    """Loads data from a single Excel file into the database."""
    logging.info(f"Processing file: {file_path}")
    try:
        df = pd.read_excel(file_path, sheet_name=None)
    except Exception as e:
        logging.error(f"Error reading Excel file {file_path}: {e}")
        return 0

    total_rows_processed = 0
    schools_cache = {} # Cache for school objects

    for sheet_name, sheet_df in df.items():
        logging.info(f"Processing sheet: {sheet_name} in {os.path.basename(file_path)}")

        # Rename columns based on updated mappings
        renamed_school_cols = {k: v for k, v in COL_MAP_SCHOOL.items() if k in sheet_df.columns}
        renamed_program_cols = {k: v for k, v in COL_MAP_PROGRAM.items() if k in sheet_df.columns}

        # Check if essential columns exist (using updated mappings)
        school_name_excel_header = next((k for k, v in COL_MAP_SCHOOL.items() if v == 'name'), '学校名称')
        program_school_name_excel_header = next((k for k, v in COL_MAP_PROGRAM.items() if v == 'school_name'), '学校名称')
        year_excel_header = next((k for k, v in COL_MAP_PROGRAM.items() if v == 'year'), '年份')
        score_excel_header = next((k for k, v in COL_MAP_PROGRAM.items() if v == 'total_score'), '总分')

        # Prioritize school name from program map if school map one doesn't exist
        if 'name' not in renamed_school_cols.values() and 'school_name' not in renamed_program_cols.values():
             logging.warning(f"Skipping sheet '{sheet_name}': Missing essential school name column ('{school_name_excel_header}' or '{program_school_name_excel_header}')")
             continue
        if 'year' not in renamed_program_cols.values():
             logging.warning(f"Skipping sheet '{sheet_name}': Missing essential year column ('{year_excel_header}')")
             continue
        # Check for total_score existence
        if 'total_score' not in renamed_program_cols.values():
            logging.warning(f"Skipping sheet '{sheet_name}': Missing essential score column ('{score_excel_header}')")
            # continue # Allow processing even if total_score is missing, maybe other scores exist

        sheet_df.rename(columns=renamed_school_cols, inplace=True)
        sheet_df.rename(columns=renamed_program_cols, inplace=True)

        rows_in_sheet = 0
        for index, row in sheet_df.iterrows():
            # Determine school name (prefer 'name' column if available, else 'school_name')
            school_name = row.get('name') if pd.notna(row.get('name')) else row.get('school_name')
            if pd.isna(school_name):
                continue # Skip if no school name

            # Prepare school data dictionary
            school_data = {col: row.get(col) for col in COL_MAP_SCHOOL.values() if col in sheet_df.columns and pd.notna(row.get(col))}
            if 'name' not in school_data: school_data['name'] = school_name # Ensure name is in the dict

            # Get or create school using cache
            school = schools_cache.get(school_name)
            if not school:
                 school = get_or_create_school(session, school_data)
                 if school:
                     schools_cache[school_name] = school
                 else:
                     continue # Skip program if school couldn't be processed

            # Prepare program data dictionary
            program_data = {col: row.get(col) for col in COL_MAP_PROGRAM.values() if col != 'school_name' and col in sheet_df.columns and pd.notna(row.get(col))}

            # *** Add Discipline Category based on Program Code ***
            program_code_str = None
            if 'program_code' in program_data:
                program_code_str = str(program_data['program_code']).strip()
                if len(program_code_str) >= 2:
                    code_prefix = program_code_str[:2]
                    program_data['discipline_category'] = DISCIPLINE_CODE_MAP.get(code_prefix, DEFAULT_DISCIPLINE_CATEGORY)
                else:
                    program_data['discipline_category'] = DEFAULT_DISCIPLINE_CATEGORY
                    # logging.debug(f"Program code '{program_code_str}' too short for category mapping.")
            else:
                # If program_code is missing, assign default category
                program_data['discipline_category'] = DEFAULT_DISCIPLINE_CATEGORY
                # logging.debug(f"Missing program_code for row {index+2}, assigning default category.")
            # *******************************************************

            # Convert types (especially scores to float)
            try:
                if 'year' in program_data: program_data['year'] = int(program_data['year'])
                score_cols = ['total_score', 'politics_score', 'english_score', 'major_score1', 'major_score2']
                for col in score_cols:
                    if col in program_data:
                        try:
                            program_data[col] = float(program_data[col])
                        except (ValueError, TypeError):
                             # Handle cases where score might be non-numeric (e.g., '--', 'N/A')
                             # logging.debug(f"Could not convert score '{program_data[col]}' to float for column {col} in row {index+2}. Setting to None.")
                             program_data[col] = None # Set to None if conversion fails

            except (ValueError, TypeError) as e:
                logging.warning(f"Skipping row {index+2} sheet '{sheet_name}': Error converting year - {e}. Data: {program_data}")
                continue

            # Add or update program line if essential data is present
            if school and school.id and program_data.get('year') and program_data.get('program_name'):
                existing_program = find_existing_program(session, school.id, program_data)
                if existing_program:
                    update_program_from_data(existing_program, program_data)
                else:
                    program_line = Program(school_id=school.id, **program_data)
                    session.add(program_line)
                rows_in_sheet += 1
            # else: # Debugging skipped rows
            #     if not school or not school.id:
            #          logging.debug(f"Skipping row {index+2} sheet '{sheet_name}': Invalid school object.")
            #     elif not program_data.get('year'):
            #          logging.debug(f"Skipping row {index+2} sheet '{sheet_name}': Missing year.")
            #     elif not program_data.get('program_name'):
            #          logging.debug(f"Skipping row {index+2} sheet '{sheet_name}': Missing program_name.")

        logging.info(f"Processed {rows_in_sheet} program rows from sheet: {sheet_name}")
        total_rows_processed += rows_in_sheet

    logging.info(f"Finished processing file: {file_path}. Total program rows added/updated: {total_rows_processed}")
    return total_rows_processed

def main():
    logging.info("Starting data loading process...")

    try:
        validate_required_env(DB_ENV_VARS, context="load_data.py database loading")
    except ValueError as exc:
        logging.error(f"Configuration error: {exc}")
        return

    engine = create_engine(DATABASE_URL)
    # Ensure tables are created based on models before loading data
    try:
        logging.info("Ensuring tables exist for configured database...")
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables checked/created successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize database tables: {e}")
        logging.error("Please check database connection details in config.py and ensure MySQL server is running and accessible.")
        return # Stop if tables can't be created

    session = SessionLocal()
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    excel_files = glob.glob(os.path.join(data_dir, '*.xlsx'))

    if not excel_files:
        logging.warning(f"No Excel files found in directory: {data_dir}")
        session.close()
        return

    logging.info(f"Found Excel files: {excel_files}")
    total_rows = 0
    for file_path in excel_files:
        try:
            rows_added = load_excel_data(session, file_path)
            session.commit() # Commit after each file
            total_rows += rows_added
        except Exception as e:
            session.rollback()
            logging.error(f"Error processing file {file_path}: {e}. Rolled back changes for this file.")

    session.close()
    logging.info(f"Data loading complete. Total program lines added across all files: {total_rows}")

if __name__ == "__main__":
    main() 