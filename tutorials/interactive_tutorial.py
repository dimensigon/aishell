#!/usr/bin/env python3
"""
AI-Shell Interactive Tutorial System
Guides users through all features with validation and progress tracking
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ProgressTracker:
    """Track tutorial progress"""

    def __init__(self, progress_file='tutorial_progress.json'):
        self.progress_file = progress_file
        self.progress = self.load_progress()

    def load_progress(self) -> Dict:
        """Load progress from file"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'started_at': datetime.now().isoformat(),
            'last_session': None,
            'completed_sections': [],
            'current_section': None,
            'scores': {}
        }

    def save_progress(self):
        """Save progress to file"""
        self.progress['last_session'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def mark_completed(self, section: str, score: int = 100):
        """Mark a section as completed"""
        if section not in self.progress['completed_sections']:
            self.progress['completed_sections'].append(section)
        self.progress['scores'][section] = score
        self.save_progress()

    def is_completed(self, section: str) -> bool:
        """Check if section is completed"""
        return section in self.progress['completed_sections']

    def get_completion_percentage(self, total_sections: int) -> float:
        """Get overall completion percentage"""
        return (len(self.progress['completed_sections']) / total_sections) * 100

class InteractiveTutorial:
    """Main tutorial system"""

    def __init__(self):
        self.tracker = ProgressTracker()
        self.sections = self.define_sections()

    def define_sections(self) -> List[Dict]:
        """Define all tutorial sections"""
        return [
            {
                'id': 'intro',
                'name': 'Introduction & Setup',
                'duration': 15,
                'level': 'Beginner',
                'lessons': [
                    {'name': 'Installation', 'validator': self.validate_installation},
                    {'name': 'Configuration', 'validator': self.validate_config},
                    {'name': 'First Connection', 'validator': self.validate_connection}
                ]
            },
            {
                'id': 'basic_queries',
                'name': 'Basic Database Queries',
                'duration': 30,
                'level': 'Beginner',
                'lessons': [
                    {'name': 'SELECT Queries', 'validator': self.validate_select},
                    {'name': 'Filtering Data', 'validator': self.validate_filter},
                    {'name': 'Sorting & Limiting', 'validator': self.validate_sort}
                ]
            },
            {
                'id': 'advanced_queries',
                'name': 'Advanced SQL Features',
                'duration': 45,
                'level': 'Intermediate',
                'lessons': [
                    {'name': 'JOINs', 'validator': self.validate_joins},
                    {'name': 'Aggregations', 'validator': self.validate_aggregations},
                    {'name': 'Subqueries', 'validator': self.validate_subqueries}
                ]
            },
            {
                'id': 'multi_db',
                'name': 'Multi-Database Operations',
                'duration': 30,
                'level': 'Intermediate',
                'lessons': [
                    {'name': 'Connecting Multiple DBs', 'validator': self.validate_multi_connect},
                    {'name': 'Cross-DB Queries', 'validator': self.validate_cross_db},
                    {'name': 'Data Transfer', 'validator': self.validate_data_transfer}
                ]
            },
            {
                'id': 'ai_features',
                'name': 'AI-Powered Features',
                'duration': 30,
                'level': 'Intermediate',
                'lessons': [
                    {'name': 'Natural Language Queries', 'validator': self.validate_nl_query},
                    {'name': 'Query Optimization', 'validator': self.validate_optimization},
                    {'name': 'Schema Understanding', 'validator': self.validate_schema_ai}
                ]
            },
            {
                'id': 'security',
                'name': 'Security & Compliance',
                'duration': 45,
                'level': 'Advanced',
                'lessons': [
                    {'name': 'RBAC Configuration', 'validator': self.validate_rbac},
                    {'name': 'Audit Logging', 'validator': self.validate_audit},
                    {'name': 'Data Encryption', 'validator': self.validate_encryption}
                ]
            },
            {
                'id': 'graphql_api',
                'name': 'GraphQL API & Web UI',
                'duration': 60,
                'level': 'Advanced',
                'lessons': [
                    {'name': 'API Setup', 'validator': self.validate_api_setup},
                    {'name': 'GraphQL Queries', 'validator': self.validate_graphql},
                    {'name': 'Dashboard Creation', 'validator': self.validate_dashboard}
                ]
            },
            {
                'id': 'performance',
                'name': 'Performance & Optimization',
                'duration': 45,
                'level': 'Expert',
                'lessons': [
                    {'name': 'Query Analysis', 'validator': self.validate_query_analysis},
                    {'name': 'Index Optimization', 'validator': self.validate_indexes},
                    {'name': 'Caching Strategies', 'validator': self.validate_caching}
                ]
            }
        ]

    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")

    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

    def show_menu(self):
        """Show main menu"""
        self.print_header("AI-Shell Interactive Tutorial")

        completion = self.tracker.get_completion_percentage(len(self.sections))
        print(f"{Colors.BOLD}Overall Progress: {completion:.1f}% Complete{Colors.ENDC}")
        print(f"Completed Sections: {len(self.tracker.progress['completed_sections'])}/{len(self.sections)}\n")

        print(f"{Colors.BOLD}Available Sections:{Colors.ENDC}\n")

        for i, section in enumerate(self.sections, 1):
            status = "✓" if self.tracker.is_completed(section['id']) else " "
            level_color = {
                'Beginner': Colors.GREEN,
                'Intermediate': Colors.YELLOW,
                'Advanced': Colors.CYAN,
                'Expert': Colors.RED
            }.get(section['level'], Colors.ENDC)

            print(f"  [{status}] {i}. {section['name']}")
            print(f"      {level_color}Level: {section['level']}{Colors.ENDC} | "
                  f"Duration: ~{section['duration']} min | "
                  f"Lessons: {len(section['lessons'])}")

        print(f"\n  {Colors.BOLD}0. Exit Tutorial{Colors.ENDC}")
        print(f"  {Colors.BOLD}R. Reset Progress{Colors.ENDC}")
        print(f"  {Colors.BOLD}S. Show Statistics{Colors.ENDC}")

    def run_section(self, section: Dict):
        """Run a tutorial section"""
        self.print_header(f"{section['name']} ({section['level']})")

        print(f"This section contains {len(section['lessons'])} lessons.")
        print(f"Estimated duration: {section['duration']} minutes\n")

        input(f"{Colors.CYAN}Press Enter to start...{Colors.ENDC}")

        completed_lessons = 0
        total_score = 0

        for i, lesson in enumerate(section['lessons'], 1):
            self.print_header(f"Lesson {i}/{len(section['lessons'])}: {lesson['name']}")

            # Run the lesson
            success, score, feedback = lesson['validator']()

            if success:
                self.print_success(f"Lesson completed! Score: {score}/100")
                completed_lessons += 1
                total_score += score
            else:
                self.print_error(f"Lesson incomplete. Score: {score}/100")

            if feedback:
                self.print_info(f"Feedback: {feedback}")

            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")

        # Calculate section score
        section_score = total_score // len(section['lessons'])

        if completed_lessons == len(section['lessons']):
            self.print_success(f"\nSection completed! Overall score: {section_score}/100")
            self.tracker.mark_completed(section['id'], section_score)
        else:
            self.print_warning(f"\nSection incomplete. Completed {completed_lessons}/{len(section['lessons'])} lessons")

    def show_statistics(self):
        """Show detailed statistics"""
        self.print_header("Tutorial Statistics")

        progress = self.tracker.progress

        print(f"Started: {progress['started_at']}")
        print(f"Last Session: {progress.get('last_session', 'N/A')}\n")

        print(f"{Colors.BOLD}Completed Sections:{Colors.ENDC}")
        for section_id in progress['completed_sections']:
            section = next((s for s in self.sections if s['id'] == section_id), None)
            if section:
                score = progress['scores'].get(section_id, 0)
                print(f"  ✓ {section['name']}: {score}/100")

        total_lessons = sum(len(s['lessons']) for s in self.sections)
        completed_lessons = sum(
            len(next((s for s in self.sections if s['id'] == sid), {'lessons': []})['lessons'])
            for sid in progress['completed_sections']
        )

        print(f"\n{Colors.BOLD}Overall Progress:{Colors.ENDC}")
        print(f"  Sections: {len(progress['completed_sections'])}/{len(self.sections)}")
        print(f"  Lessons: {completed_lessons}/{total_lessons}")
        print(f"  Average Score: {sum(progress['scores'].values()) / max(len(progress['scores']), 1):.1f}/100")

        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")

    def reset_progress(self):
        """Reset all progress"""
        confirm = input(f"{Colors.YELLOW}Are you sure you want to reset all progress? (yes/no): {Colors.ENDC}")
        if confirm.lower() == 'yes':
            os.remove(self.tracker.progress_file)
            self.tracker = ProgressTracker()
            self.print_success("Progress reset successfully!")
        else:
            self.print_info("Reset cancelled")

    def run(self):
        """Main tutorial loop"""
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            self.show_menu()

            choice = input(f"\n{Colors.BOLD}Select an option: {Colors.ENDC}").strip()

            if choice == '0':
                print(f"\n{Colors.GREEN}Thank you for using AI-Shell Tutorial!{Colors.ENDC}")
                break
            elif choice.upper() == 'R':
                self.reset_progress()
            elif choice.upper() == 'S':
                self.show_statistics()
            elif choice.isdigit() and 1 <= int(choice) <= len(self.sections):
                section = self.sections[int(choice) - 1]
                self.run_section(section)
            else:
                self.print_error("Invalid choice. Please try again.")
                time.sleep(1)

    # ==================== Validators ====================

    def validate_installation(self) -> Tuple[bool, int, str]:
        """Validate AI-Shell installation"""
        self.print_info("Checking AI-Shell installation...")

        try:
            result = subprocess.run(
                ['ai-shell', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                self.print_success(f"AI-Shell installed: {result.stdout.strip()}")
                return (True, 100, "Installation verified successfully")
            else:
                return (False, 0, "AI-Shell not found. Please install it first.")

        except Exception as e:
            return (False, 0, f"Error checking installation: {e}")

    def validate_config(self) -> Tuple[bool, int, str]:
        """Validate configuration file"""
        self.print_info("Checking configuration...")

        config_paths = [
            os.path.expanduser('~/.ai-shell/config.yaml'),
            'config/config.yaml',
            'ai-shell-config.yaml'
        ]

        for path in config_paths:
            if os.path.exists(path):
                self.print_success(f"Configuration found: {path}")
                return (True, 100, "Configuration file exists")

        self.print_warning("No configuration file found")
        create = input("Would you like to create a basic configuration? (y/n): ")

        if create.lower() == 'y':
            config_dir = os.path.expanduser('~/.ai-shell')
            os.makedirs(config_dir, exist_ok=True)

            config_content = """
# AI-Shell Configuration
databases:
  sample_db:
    type: sqlite
    path: ./sample.db

general:
  output_format: table
  max_rows: 100
"""
            config_path = os.path.join(config_dir, 'config.yaml')
            with open(config_path, 'w') as f:
                f.write(config_content)

            self.print_success(f"Configuration created: {config_path}")
            return (True, 80, "Configuration created successfully")

        return (False, 50, "Configuration not set up")

    def validate_connection(self) -> Tuple[bool, int, str]:
        """Validate database connection"""
        self.print_info("Testing database connection...")

        print("\nTry connecting to a database:")
        print("Example: ai-shell --db sqlite:///sample.db")
        print("\nEnter your connection command (or 'skip' to skip):")

        command = input("> ").strip()

        if command.lower() == 'skip':
            return (False, 0, "Connection test skipped")

        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=10
            )

            if "Connected" in result.stdout or result.returncode == 0:
                self.print_success("Connection successful!")
                return (True, 100, "Database connection established")
            else:
                return (False, 50, f"Connection failed: {result.stderr}")

        except Exception as e:
            return (False, 0, f"Error testing connection: {e}")

    def validate_select(self) -> Tuple[bool, int, str]:
        """Validate SELECT query"""
        self.print_info("Practice SELECT queries...")

        print("\nWrite a SELECT query to retrieve all columns from a table")
        print("Example: SELECT * FROM users LIMIT 10")

        query = input("\nYour query: ").strip()

        score = 0
        feedback = []

        # Check query structure
        if re.match(r'SELECT\s+', query, re.IGNORECASE):
            score += 30
            feedback.append("✓ SELECT keyword used")
        else:
            feedback.append("✗ Missing SELECT keyword")

        if re.search(r'FROM\s+\w+', query, re.IGNORECASE):
            score += 30
            feedback.append("✓ FROM clause present")
        else:
            feedback.append("✗ Missing FROM clause")

        if 'LIMIT' in query.upper() or 'TOP' in query.upper():
            score += 20
            feedback.append("✓ Result limiting used")

        if query.strip().endswith(';'):
            score += 20
            feedback.append("✓ Query terminated with semicolon")

        success = score >= 60
        return (success, score, " | ".join(feedback))

    def validate_filter(self) -> Tuple[bool, int, str]:
        """Validate filtering with WHERE clause"""
        self.print_info("Practice filtering data...")

        print("\nWrite a query with a WHERE clause to filter results")
        print("Example: SELECT * FROM orders WHERE total > 100")

        query = input("\nYour query: ").strip()

        score = 0
        feedback = []

        if re.search(r'WHERE\s+', query, re.IGNORECASE):
            score += 50
            feedback.append("✓ WHERE clause used")
        else:
            feedback.append("✗ Missing WHERE clause")

        operators = ['=', '>', '<', '>=', '<=', '!=', 'LIKE', 'IN', 'BETWEEN']
        if any(op in query.upper() for op in operators):
            score += 30
            feedback.append("✓ Comparison operator used")

        if 'AND' in query.upper() or 'OR' in query.upper():
            score += 20
            feedback.append("✓ Logical operator used")

        success = score >= 50
        return (success, score, " | ".join(feedback))

    def validate_sort(self) -> Tuple[bool, int, str]:
        """Validate sorting and limiting"""
        self.print_info("Practice sorting and limiting results...")

        print("\nWrite a query that sorts results and limits the output")
        print("Example: SELECT * FROM products ORDER BY price DESC LIMIT 10")

        query = input("\nYour query: ").strip()

        score = 0
        feedback = []

        if re.search(r'ORDER\s+BY\s+\w+', query, re.IGNORECASE):
            score += 50
            feedback.append("✓ ORDER BY clause used")
        else:
            feedback.append("✗ Missing ORDER BY clause")

        if 'DESC' in query.upper() or 'ASC' in query.upper():
            score += 20
            feedback.append("✓ Sort direction specified")

        if 'LIMIT' in query.upper():
            score += 30
            feedback.append("✓ LIMIT clause used")

        success = score >= 70
        return (success, score, " | ".join(feedback))

    def validate_joins(self) -> Tuple[bool, int, str]:
        """Validate JOIN queries"""
        self.print_info("Practice JOIN operations...")

        print("\nWrite a query that joins two tables")
        print("Example: SELECT o.*, c.name FROM orders o JOIN customers c ON o.customer_id = c.id")

        query = input("\nYour query: ").strip()

        score = 0
        feedback = []

        join_types = ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN']
        if any(jt in query.upper() for jt in join_types):
            score += 40
            feedback.append("✓ JOIN used")
        else:
            feedback.append("✗ Missing JOIN")

        if re.search(r'ON\s+\w+\.\w+\s*=\s*\w+\.\w+', query, re.IGNORECASE):
            score += 40
            feedback.append("✓ ON condition specified")
        else:
            feedback.append("✗ Missing or incorrect ON condition")

        if re.search(r'\w+\.\w+', query):
            score += 20
            feedback.append("✓ Table aliases used")

        success = score >= 60
        return (success, score, " | ".join(feedback))

    def validate_aggregations(self) -> Tuple[bool, int, str]:
        """Validate aggregation functions"""
        self.print_info("Practice aggregation functions...")

        print("\nWrite a query using aggregation functions")
        print("Example: SELECT COUNT(*), AVG(price) FROM products GROUP BY category")

        query = input("\nYour query: ").strip()

        score = 0
        feedback = []

        agg_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']
        used_functions = [fn for fn in agg_functions if fn in query.upper()]

        if used_functions:
            score += 40
            feedback.append(f"✓ Aggregation functions used: {', '.join(used_functions)}")
        else:
            feedback.append("✗ No aggregation functions found")

        if 'GROUP BY' in query.upper():
            score += 40
            feedback.append("✓ GROUP BY clause used")

        if 'HAVING' in query.upper():
            score += 20
            feedback.append("✓ HAVING clause used (bonus!)")

        success = score >= 60
        return (success, score, " | ".join(feedback))

    def validate_subqueries(self) -> Tuple[bool, int, str]:
        """Validate subquery usage"""
        self.print_info("Practice subqueries...")

        print("\nWrite a query that uses a subquery")
        print("Example: SELECT * FROM orders WHERE customer_id IN (SELECT id FROM customers WHERE country = 'USA')")

        query = input("\nYour query: ").strip()

        score = 0
        feedback = []

        # Count parentheses to detect subqueries
        if query.count('(') >= 2 and query.count(')') >= 2:
            score += 50
            feedback.append("✓ Subquery detected")
        else:
            feedback.append("✗ No subquery found")

        subquery_keywords = ['IN', 'EXISTS', 'ANY', 'ALL']
        if any(kw in query.upper() for kw in subquery_keywords):
            score += 30
            feedback.append("✓ Subquery operator used")

        if query.upper().count('SELECT') >= 2:
            score += 20
            feedback.append("✓ Multiple SELECT statements")

        success = score >= 60
        return (success, score, " | ".join(feedback))

    # Placeholder validators for remaining sections
    def validate_multi_connect(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Multiple DB Connection")

    def validate_cross_db(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Cross-DB Query")

    def validate_data_transfer(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Data Transfer")

    def validate_nl_query(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Natural Language Query")

    def validate_optimization(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Query Optimization")

    def validate_schema_ai(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Schema Understanding")

    def validate_rbac(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("RBAC Configuration")

    def validate_audit(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Audit Logging")

    def validate_encryption(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Data Encryption")

    def validate_api_setup(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("API Setup")

    def validate_graphql(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("GraphQL Queries")

    def validate_dashboard(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Dashboard Creation")

    def validate_query_analysis(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Query Analysis")

    def validate_indexes(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Index Optimization")

    def validate_caching(self) -> Tuple[bool, int, str]:
        return self._placeholder_validator("Caching Strategies")

    def _placeholder_validator(self, lesson_name: str) -> Tuple[bool, int, str]:
        """Placeholder for lessons without full validation"""
        self.print_info(f"Learning about {lesson_name}...")
        print(f"\nThis is a hands-on lesson. Please follow the tutorial documentation for {lesson_name}.")
        print("Have you completed the exercises? (y/n): ")

        completed = input("> ").strip().lower()

        if completed == 'y':
            return (True, 85, f"{lesson_name} completed manually")
        else:
            return (False, 50, f"{lesson_name} practice recommended")

def main():
    """Main entry point"""
    try:
        tutorial = InteractiveTutorial()
        tutorial.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tutorial interrupted. Progress has been saved.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}An error occurred: {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == '__main__':
    main()
