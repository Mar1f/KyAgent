from sqlalchemy.orm import sessionmaker, joinedload
from app.database.models import engine, School, Program, SessionLocal
import pandas as pd
import os
from datetime import datetime

# Create session
Session = sessionmaker(bind=engine)

class DatabaseManager:
    def __init__(self):
        # Use the SessionLocal factory to create session instances
        self.session = SessionLocal()
    
    def close(self):
        """Close the database session"""
        self.session.close()
    
    # --- School methods --- 
    def get_all_schools(self):
        """Get all schools"""
        return self.session.query(School).order_by(School.name).all()
    
    def get_school_by_name(self, name):
        """Get school by name"""
        return self.session.query(School).filter(School.name == name).first()
    
    def get_school_by_id(self, school_id):
        """Get school by id"""
        return self.session.query(School).filter(School.id == school_id).first()
    
    # --- Program methods --- 
    def get_all_programs(self):
        """Get all programs (potentially large, consider filtering)"""
        # Eager load the related school to avoid N+1 queries later
        return self.session.query(Program).options(joinedload(Program.school)).order_by(Program.school_id, Program.year, Program.program_name).all()
    
    def get_program_by_code_and_year(self, school_id, code, year):
        """Get program by school, code, and year"""
        return self.session.query(Program).filter(
            Program.school_id == school_id,
            Program.program_code == code,
            Program.year == year
        ).first()
    
    def get_programs_by_school(self, school_name, years=None):
        """Get all programs for a specific school, optionally filtered by years"""
        school = self.get_school_by_name(school_name)
        if not school:
            return []
        query = self.session.query(Program).filter(Program.school_id == school.id)
        if years:
            query = query.filter(Program.year.in_(years))
        return query.options(joinedload(Program.school)).order_by(Program.year.desc(), Program.program_name).all()
    
    def get_programs_by_name(self, program_name, years=None):
        """Get all programs matching a name, optionally filtered by years"""
        query = self.session.query(Program).filter(Program.program_name.like(f'%{program_name}%'))
        if years:
            query = query.filter(Program.year.in_(years))
        return query.options(joinedload(Program.school)).order_by(Program.school_id, Program.year.desc()).all()
    
    def get_programs_by_discipline(self, discipline_category, years=None):
        """Get all programs for a specific discipline category"""
        query = self.session.query(Program).filter(Program.discipline_category == discipline_category)
        if years:
            query = query.filter(Program.year.in_(years))
        return query.options(joinedload(Program.school)).order_by(Program.school_id, Program.year.desc()).all()
    
    # --- Combined Queries for Analysis --- 
    def get_admission_data_for_school(self, school_name, years=None):
        """Get structured admission data (programs) for a specific school."""
        school = self.get_school_by_name(school_name)
        if not school:
            return pd.DataFrame() # Return empty DataFrame if school not found
        
        query = self.session.query(Program).filter(Program.school_id == school.id)
        if years:
            query = query.filter(Program.year.in_(years))
            
        programs = query.order_by(Program.year.desc(), Program.program_name).all()
        
        # Convert to DataFrame
        data = [{
            "year": p.year,
            "program_code": p.program_code,
            "program_name": p.program_name,
            "program_type": p.program_type,
            "discipline_category": p.discipline_category,
            "total_score": p.total_score,
            "politics_score": p.politics_score,
            "english_score": p.english_score,
            "major_score1": p.major_score1,
            "major_score2": p.major_score2,
            "notes": p.notes
        } for p in programs]
        
        return pd.DataFrame(data)
    
    def get_admission_data_for_program(self, program_name, years=None):
        """Get structured admission data for a specific program name across schools."""
        query = self.session.query(Program).filter(Program.program_name.like(f'%{program_name}%'))
        if years:
            query = query.filter(Program.year.in_(years))
            
        # Eager load school data
        programs = query.options(joinedload(Program.school)).order_by(Program.year.desc(), Program.school_id).all()
        
        # Convert to DataFrame
        data = [{
            "year": p.year,
            "school_name": p.school.name if p.school else "Unknown",
            "school_province": p.school.province if p.school else "Unknown",
            "program_code": p.program_code,
            "program_name": p.program_name,
            "program_type": p.program_type,
            "discipline_category": p.discipline_category,
            "total_score": p.total_score,
            "politics_score": p.politics_score,
            "english_score": p.english_score,
            "major_score1": p.major_score1,
            "major_score2": p.major_score2,
            "notes": p.notes
        } for p in programs]
        
        return pd.DataFrame(data)
        
    def get_all_program_disciplines(self):
        """Get distinct discipline categories from the programs table."""
        disciplines = self.session.query(Program.discipline_category).distinct().order_by(Program.discipline_category).all()
        return [d[0] for d in disciplines if d[0]] # Return list of non-null disciplines

    # The complex data loading from CSV is no longer needed here.
    # def load_data_from_csv(self, csv_file):
    #     ... 

    # --- Search History Methods (If you want to keep them) --- 
    # def add_search_query(self, query_text, source="OpenAI"):
    #     ...
    # def add_search_result(self, query_id, result_data):
    #     ...
    # def get_search_results(self, query_id):
    #     ... 