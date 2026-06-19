from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, joinedload
from app.database.models import engine, School, Program, SessionLocal, User
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
    
    # --- User methods ---
    def get_all_users(self):
        """Get all users for authentication."""
        return self.session.query(User).order_by(User.username).all()

    def get_user_by_username(self, username):
        """Get a user by username."""
        return self.session.query(User).filter(User.username == username).first()

    def create_user(self, name, username, hashed_password):
        """Create and persist a new user."""
        user = User(name=name, username=username, password=hashed_password)
        self.session.add(user)
        self.session.commit()
        return user

    def rollback(self):
        """Rollback the current transaction."""
        self.session.rollback()

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

    def find_existing_program(self, school_id, year, program_code=None, program_name=None, program_type=None):
        """Find an existing program row for idempotent imports."""
        if not school_id or not year:
            return None

        query = self.session.query(Program).filter(
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

    def get_distinct_program_names(self):
        """Get sorted distinct program names."""
        program_names = self.session.query(Program.program_name).distinct().order_by(Program.program_name).all()
        return sorted([p[0] for p in program_names if p[0]])

    def get_available_years(self):
        """Get distinct years present in the program data."""
        years = self.session.query(Program.year).distinct().order_by(Program.year.desc()).all()
        return [y[0] for y in years if y[0]]

    def get_discipline_browsing_data(self, discipline_category, years=None):
        """Get discipline browsing rows formatted for the analysis page."""
        programs = self.get_programs_by_discipline(discipline_category, years)
        return pd.DataFrame([
            {
                "年份": p.year,
                "学校": p.school.name if p.school else "N/A",
                "专业代码": p.program_code,
                "专业名称": p.program_name,
                "学习方式": p.program_type,
                "总分": p.total_score,
                "政治": p.politics_score,
                "外语": p.english_score,
                "业务课一": p.major_score1,
                "业务课二": p.major_score2,
            }
            for p in programs
        ])

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

    def get_discipline_counts(self):
        """Get aggregated counts by discipline category."""
        rows = self.session.query(
            Program.discipline_category,
            func.count(Program.id)
        ).filter(
            Program.discipline_category.isnot(None)
        ).group_by(
            Program.discipline_category
        ).order_by(
            func.count(Program.id).desc(),
            Program.discipline_category.asc()
        ).all()

        return pd.DataFrame([
            {"discipline": discipline, "count": count}
            for discipline, count in rows
        ])

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