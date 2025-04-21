use graduate_info;
CREATE TABLE users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        username VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL -- This will store the hashed password
        -- You might want to add an email column later for password recovery
        -- email VARCHAR(255) UNIQUE
    );


use graduate_info;
SELECT programs.year, programs.program_name, programs.program_type, programs.total_score, programs.politics_score, programs.english_score, programs.major_score1, programs.major_score2 FROM programs JOIN schools ON schools.id = programs.school_id WHERE schools.name = '南京邮电大学' AND programs.program_name LIKE '%计算机技术%' AND programs.year = 2023;