from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text, VARCHAR, DECIMAL
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.orm import declarative_base
import sys
import os

# Add project root to path if necessary (though config import should work if run from root)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app_config import DATABASE_URL

Base = declarative_base()

# Using user's table name 'schools'
class School(Base):
    __tablename__ = 'schools'

    id = Column(Integer, primary_key=True)
    # Using user's column names
    name = Column(VARCHAR(100), nullable=False, unique=True, index=True)
    province = Column(VARCHAR(50))
    type = Column(VARCHAR(50)) # Corresponds to user's 'type'
    website = Column(VARCHAR(255))
    grad_website = Column(VARCHAR(255)) # User's 'grad_website'
    phone = Column(VARCHAR(50))
    email = Column(VARCHAR(100))
    address = Column(VARCHAR(255))
    affiliation = Column(VARCHAR(100))
    master_programs = Column(Integer) # User's 'master_programs'
    doctoral_programs = Column(Integer) # User's 'doctoral_programs'
    key_disciplines = Column(Integer) # User's 'key_disciplines' (assuming count)
    key_labs = Column(Integer) # User's 'key_labs' (assuming count)

    # Relationship name updated to reflect the other table's name
    programs = relationship("Program", back_populates="school")

    def __repr__(self):
        return f"<School(name='{self.name}')>"

# Using user's table name 'programs'
class Program(Base):
    __tablename__ = 'programs'

    id = Column(Integer, primary_key=True)
    school_id = Column(Integer, ForeignKey('schools.id'), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    # Recommended addition
    discipline_category = Column(VARCHAR(100), index=True) # e.g., '哲学', '经济学', '法学', '理学', '工学'...
    # Using user's column names
    program_type = Column(VARCHAR(50), index=True) # e.g., '学硕', '专硕'
    program_code = Column(VARCHAR(20), index=True)
    program_name = Column(VARCHAR(100), index=True)
    # Recommended type change to FLOAT or DECIMAL for scores
    total_score = Column(Float) # User's 'total_score'
    politics_score = Column(Float)
    english_score = Column(Float)
    major_score1 = Column(Float)
    major_score2 = Column(Float)
    notes = Column(Text) # User's 'notes'

    school = relationship("School", back_populates="programs")

    def __repr__(self):
        return f"<Program(year={self.year}, school_id={self.school_id}, name='{self.program_name}', score={self.total_score})>"

class User(Base):
    __tablename__ = 'users' # Make sure this matches your table name

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False) # Stores the hashed password

    def __repr__(self):
        return f"<User(username='{self.username}', name='{self.name}')>"

# Engine setup
engine = create_engine(DATABASE_URL, echo=False) # Set echo=True for debugging SQL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Create tables
    # This will create tables based on the Base metadata, reflecting the classes defined above
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Initializing database based on models.py...")
    # You might want to comment out init_db() call here if you manage table creation separately
    # init_db()
    print("Database initialization script finished. Ensure your DB schema matches these models.")
    # print(f"Using database: {DATABASE_URL}")