#!/usr/bin/env python3
"""
AIShell Tutorial Progress Tracker

Track your progress through the AIShell tutorial series with gamified achievements,
badges, and completion certificates.

Features:
- Track completion of each tutorial section
- Award badges for milestones
- Generate completion certificates
- Save/load progress from file
- Display progress statistics
- Provide personalized learning recommendations

Usage:
    python tutorials/progress_tracker.py
    python tutorials/progress_tracker.py --complete 01
    python tutorials/progress_tracker.py --status
    python tutorials/progress_tracker.py --certificate
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict


# ============================================================================
# Data Models
# ============================================================================

class BadgeLevel(Enum):
    BRONZE = "🥉 Bronze"
    SILVER = "🥈 Silver"
    GOLD = "🥇 Gold"
    PLATINUM = "💎 Platinum"


@dataclass
class Badge:
    """Achievement badge"""
    id: str
    name: str
    description: str
    level: BadgeLevel
    icon: str
    earned_at: Optional[str] = None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'level': self.level.value,
            'icon': self.icon,
            'earned_at': self.earned_at
        }


@dataclass
class TutorialSection:
    """A section within a tutorial"""
    section_id: str
    section_name: str
    description: str
    completed: bool = False
    completed_at: Optional[str] = None
    notes: str = ""

    def to_dict(self):
        return {
            'section_id': self.section_id,
            'section_name': self.section_name,
            'description': self.description,
            'completed': self.completed,
            'completed_at': self.completed_at,
            'notes': self.notes
        }


@dataclass
class Tutorial:
    """A complete tutorial"""
    tutorial_id: str
    tutorial_name: str
    level: str  # beginner, intermediate, advanced
    estimated_time: int  # minutes
    prerequisites: List[str] = field(default_factory=list)
    sections: List[TutorialSection] = field(default_factory=list)
    completed: bool = False
    completed_at: Optional[str] = None

    def completion_percentage(self) -> float:
        if not self.sections:
            return 0.0
        completed = sum(1 for s in self.sections if s.completed)
        return (completed / len(self.sections)) * 100

    def to_dict(self):
        return {
            'tutorial_id': self.tutorial_id,
            'tutorial_name': self.tutorial_name,
            'level': self.level,
            'estimated_time': self.estimated_time,
            'prerequisites': self.prerequisites,
            'sections': [s.to_dict() for s in self.sections],
            'completed': self.completed,
            'completed_at': self.completed_at
        }


@dataclass
class LearningProgress:
    """Overall learning progress"""
    user_name: str
    started_at: str
    last_updated: str
    tutorials: List[Tutorial] = field(default_factory=list)
    badges: List[Badge] = field(default_factory=list)
    total_time_spent: int = 0  # minutes
    streak_days: int = 0
    last_activity_date: Optional[str] = None

    def overall_completion(self) -> float:
        if not self.tutorials:
            return 0.0
        completed = sum(1 for t in self.tutorials if t.completed)
        return (completed / len(self.tutorials)) * 100

    def to_dict(self):
        return {
            'user_name': self.user_name,
            'started_at': self.started_at,
            'last_updated': self.last_updated,
            'tutorials': [t.to_dict() for t in self.tutorials],
            'badges': [b.to_dict() for b in self.badges],
            'total_time_spent': self.total_time_spent,
            'streak_days': self.streak_days,
            'last_activity_date': self.last_activity_date
        }


# ============================================================================
# Tutorial Definitions
# ============================================================================

def create_default_tutorials() -> List[Tutorial]:
    """Create the default AIShell tutorial structure"""

    tutorials = [
        Tutorial(
            tutorial_id="00",
            tutorial_name="Getting Started",
            level="beginner",
            estimated_time=20,
            prerequisites=[],
            sections=[
                TutorialSection("00-1", "Installation", "Install AIShell and dependencies"),
                TutorialSection("00-2", "Configuration", "Set up initial configuration"),
                TutorialSection("00-3", "First Commands", "Run your first AIShell commands"),
                TutorialSection("00-4", "Project Structure", "Understand the project layout")
            ]
        ),
        Tutorial(
            tutorial_id="01",
            tutorial_name="Health Check System",
            level="beginner",
            estimated_time=30,
            prerequisites=[],
            sections=[
                TutorialSection("01-1", "Introduction", "Understanding health checks"),
                TutorialSection("01-2", "Quick Start", "Your first health check"),
                TutorialSection("01-3", "Async Patterns", "Async/await in health checks"),
                TutorialSection("01-4", "Parallel Execution", "Running checks in parallel"),
                TutorialSection("01-5", "Custom Checks", "Building custom health checks"),
                TutorialSection("01-6", "Error Handling", "Handling check failures"),
                TutorialSection("01-7", "Hands-On Project", "Complete health monitoring system")
            ]
        ),
        Tutorial(
            tutorial_id="02",
            tutorial_name="Building Custom Agents",
            level="intermediate",
            estimated_time=60,
            prerequisites=["01"],
            sections=[
                TutorialSection("02-1", "Agent Architecture", "Understanding agent design"),
                TutorialSection("02-2", "Planning Logic", "Implementing plan() method"),
                TutorialSection("02-3", "Execution Logic", "Implementing execute_step()"),
                TutorialSection("02-4", "State Management", "Persisting agent state"),
                TutorialSection("02-5", "Safety Validation", "Implementing validate_safety()"),
                TutorialSection("02-6", "Error Recovery", "Handling failures and rollbacks"),
                TutorialSection("02-7", "Complete Example", "DatabaseMaintenanceAgent walkthrough"),
                TutorialSection("02-8", "Hands-On Projects", "Build 3 production agents")
            ]
        ),
        Tutorial(
            tutorial_id="03",
            tutorial_name="Tool Registry System",
            level="intermediate",
            estimated_time=45,
            prerequisites=["01"],
            sections=[
                TutorialSection("03-1", "Tool Registry Basics", "Understanding the tool registry"),
                TutorialSection("03-2", "Creating Tools", "Build your first tool"),
                TutorialSection("03-3", "Parameter Validation", "JSON Schema validation"),
                TutorialSection("03-4", "Risk Levels", "Understanding risk classification"),
                TutorialSection("03-5", "Capabilities", "Permission-based tool access"),
                TutorialSection("03-6", "LLM Integration", "Tools for LLM agents"),
                TutorialSection("03-7", "Rate Limiting", "Preventing resource exhaustion"),
                TutorialSection("03-8", "Complete Example", "Database optimization tool")
            ]
        ),
        Tutorial(
            tutorial_id="04",
            tutorial_name="Safety & Approval System",
            level="advanced",
            estimated_time=40,
            prerequisites=["02", "03"],
            sections=[
                TutorialSection("04-1", "Safety Levels", "Strict, moderate, permissive modes"),
                TutorialSection("04-2", "Risk Assessment", "Automatic risk evaluation"),
                TutorialSection("04-3", "Approval Workflows", "Human-in-the-loop approvals"),
                TutorialSection("04-4", "SQL Risk Analysis", "Detecting dangerous queries"),
                TutorialSection("04-5", "Custom Callbacks", "Automated approval logic"),
                TutorialSection("04-6", "Audit Trail", "Compliance and logging"),
                TutorialSection("04-7", "Production Deployment", "Security hardening")
            ]
        ),
        Tutorial(
            tutorial_id="05",
            tutorial_name="Complete Workflow Example",
            level="advanced",
            estimated_time=90,
            prerequisites=["01", "02", "03", "04"],
            sections=[
                TutorialSection("05-1", "Overview", "Understanding the maintenance workflow"),
                TutorialSection("05-2", "Health Check System", "Matrix-style startup screen"),
                TutorialSection("05-3", "Agent Implementation", "PerformanceAnalysisAgent"),
                TutorialSection("05-4", "Custom Tools", "Database maintenance tools"),
                TutorialSection("05-5", "UI Components", "Textual-based interface"),
                TutorialSection("05-6", "Configuration", "YAML configuration files"),
                TutorialSection("05-7", "Running the Workflow", "End-to-end execution"),
                TutorialSection("05-8", "Customization", "Adapting to your needs")
            ]
        ),
        Tutorial(
            tutorial_id="06",
            tutorial_name="Quick Reference",
            level="intermediate",
            estimated_time=15,
            prerequisites=[],
            sections=[
                TutorialSection("06-1", "Agent Patterns", "Common agent structures"),
                TutorialSection("06-2", "Tool Patterns", "Tool registration patterns"),
                TutorialSection("06-3", "Safety Patterns", "Safety validation shortcuts"),
                TutorialSection("06-4", "CLI Commands", "Useful command reference"),
                TutorialSection("06-5", "Cheat Sheet", "Quick syntax reference")
            ]
        )
    ]

    return tutorials


# ============================================================================
# Badge System
# ============================================================================

class BadgeSystem:
    """Manages achievement badges"""

    @staticmethod
    def get_all_badges() -> List[Badge]:
        """Define all available badges"""
        return [
            # Tutorial completion badges
            Badge(
                id="first_steps",
                name="First Steps",
                description="Complete Tutorial 00: Getting Started",
                level=BadgeLevel.BRONZE,
                icon="👣"
            ),
            Badge(
                id="health_check_master",
                name="Health Check Master",
                description="Complete Tutorial 01: Health Checks",
                level=BadgeLevel.BRONZE,
                icon="🏥"
            ),
            Badge(
                id="agent_builder",
                name="Agent Builder",
                description="Complete Tutorial 02: Building Custom Agents",
                level=BadgeLevel.SILVER,
                icon="🤖"
            ),
            Badge(
                id="tool_craftsman",
                name="Tool Craftsman",
                description="Complete Tutorial 03: Tool Registry",
                level=BadgeLevel.SILVER,
                icon="🔧"
            ),
            Badge(
                id="safety_expert",
                name="Safety Expert",
                description="Complete Tutorial 04: Safety & Approvals",
                level=BadgeLevel.GOLD,
                icon="🛡️"
            ),
            Badge(
                id="workflow_master",
                name="Workflow Master",
                description="Complete Tutorial 05: Complete Workflow",
                level=BadgeLevel.GOLD,
                icon="⚡"
            ),

            # Milestone badges
            Badge(
                id="quick_learner",
                name="Quick Learner",
                description="Complete any tutorial in under 30 minutes",
                level=BadgeLevel.BRONZE,
                icon="⚡"
            ),
            Badge(
                id="foundation_complete",
                name="Foundation Complete",
                description="Complete all beginner tutorials",
                level=BadgeLevel.SILVER,
                icon="🏗️"
            ),
            Badge(
                id="intermediate_graduate",
                name="Intermediate Graduate",
                description="Complete all intermediate tutorials",
                level=BadgeLevel.GOLD,
                icon="🎓"
            ),
            Badge(
                id="advanced_practitioner",
                name="Advanced Practitioner",
                description="Complete all advanced tutorials",
                level=BadgeLevel.PLATINUM,
                icon="💎"
            ),
            Badge(
                id="aishell_expert",
                name="AIShell Expert",
                description="Complete ALL tutorials",
                level=BadgeLevel.PLATINUM,
                icon="🏆"
            ),

            # Streak badges
            Badge(
                id="dedicated_learner",
                name="Dedicated Learner",
                description="Maintain a 3-day learning streak",
                level=BadgeLevel.BRONZE,
                icon="📅"
            ),
            Badge(
                id="persistent_student",
                name="Persistent Student",
                description="Maintain a 7-day learning streak",
                level=BadgeLevel.SILVER,
                icon="🔥"
            ),
            Badge(
                id="marathon_runner",
                name="Marathon Runner",
                description="Spend 5+ hours learning",
                level=BadgeLevel.GOLD,
                icon="🏃"
            )
        ]

    @staticmethod
    def check_earned_badges(progress: LearningProgress) -> List[Badge]:
        """Check which badges should be awarded"""
        earned = []
        all_badges = BadgeSystem.get_all_badges()
        existing_badge_ids = {b.id for b in progress.badges if b.earned_at}

        for badge in all_badges:
            if badge.id in existing_badge_ids:
                continue  # Already earned

            # Check badge conditions
            if BadgeSystem._should_award_badge(badge, progress):
                badge.earned_at = datetime.now().isoformat()
                earned.append(badge)

        return earned

    @staticmethod
    def _should_award_badge(badge: Badge, progress: LearningProgress) -> bool:
        """Check if badge conditions are met"""
        tutorial_map = {t.tutorial_id: t for t in progress.tutorials}

        # Tutorial completion badges
        if badge.id == "first_steps":
            return tutorial_map.get("00", Tutorial("00", "", "beginner", 0)).completed
        elif badge.id == "health_check_master":
            return tutorial_map.get("01", Tutorial("01", "", "beginner", 0)).completed
        elif badge.id == "agent_builder":
            return tutorial_map.get("02", Tutorial("02", "", "intermediate", 0)).completed
        elif badge.id == "tool_craftsman":
            return tutorial_map.get("03", Tutorial("03", "", "intermediate", 0)).completed
        elif badge.id == "safety_expert":
            return tutorial_map.get("04", Tutorial("04", "", "advanced", 0)).completed
        elif badge.id == "workflow_master":
            return tutorial_map.get("05", Tutorial("05", "", "advanced", 0)).completed

        # Milestone badges
        elif badge.id == "foundation_complete":
            return all(t.completed for t in progress.tutorials if t.level == "beginner")
        elif badge.id == "intermediate_graduate":
            return all(t.completed for t in progress.tutorials if t.level == "intermediate")
        elif badge.id == "advanced_practitioner":
            return all(t.completed for t in progress.tutorials if t.level == "advanced")
        elif badge.id == "aishell_expert":
            return all(t.completed for t in progress.tutorials)

        # Streak badges
        elif badge.id == "dedicated_learner":
            return progress.streak_days >= 3
        elif badge.id == "persistent_student":
            return progress.streak_days >= 7
        elif badge.id == "marathon_runner":
            return progress.total_time_spent >= 300  # 5 hours

        return False


# ============================================================================
# Progress Tracker
# ============================================================================

class ProgressTracker:
    """Main progress tracking system"""

    def __init__(self, progress_file: str = None):
        self.progress_file = progress_file or str(Path.home() / ".aishell_progress.json")
        self.progress: Optional[LearningProgress] = None

    def initialize(self, user_name: str = "Student"):
        """Initialize new progress"""
        self.progress = LearningProgress(
            user_name=user_name,
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            tutorials=create_default_tutorials(),
            badges=[],
            total_time_spent=0,
            streak_days=1,
            last_activity_date=datetime.now().date().isoformat()
        )

    def load(self) -> bool:
        """Load progress from file"""
        if not os.path.exists(self.progress_file):
            return False

        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)

            # Reconstruct progress from JSON
            tutorials = [self._dict_to_tutorial(t) for t in data['tutorials']]
            badges = [self._dict_to_badge(b) for b in data['badges']]

            self.progress = LearningProgress(
                user_name=data['user_name'],
                started_at=data['started_at'],
                last_updated=data['last_updated'],
                tutorials=tutorials,
                badges=badges,
                total_time_spent=data.get('total_time_spent', 0),
                streak_days=data.get('streak_days', 0),
                last_activity_date=data.get('last_activity_date')
            )

            return True

        except Exception as e:
            print(f"Error loading progress: {e}")
            return False

    def save(self):
        """Save progress to file"""
        if not self.progress:
            return

        self.progress.last_updated = datetime.now().isoformat()

        # Update streak
        today = datetime.now().date().isoformat()
        if self.progress.last_activity_date != today:
            last_date = datetime.fromisoformat(self.progress.last_activity_date).date() if self.progress.last_activity_date else datetime.now().date()
            if (datetime.now().date() - last_date).days == 1:
                self.progress.streak_days += 1
            elif (datetime.now().date() - last_date).days > 1:
                self.progress.streak_days = 1
            self.progress.last_activity_date = today

        with open(self.progress_file, 'w') as f:
            json.dump(self.progress.to_dict(), f, indent=2)

    def complete_section(self, tutorial_id: str, section_id: str):
        """Mark a section as completed"""
        if not self.progress:
            return

        for tutorial in self.progress.tutorials:
            if tutorial.tutorial_id == tutorial_id:
                for section in tutorial.sections:
                    if section.section_id == section_id:
                        section.completed = True
                        section.completed_at = datetime.now().isoformat()

                # Check if tutorial is complete
                if all(s.completed for s in tutorial.sections):
                    tutorial.completed = True
                    tutorial.completed_at = datetime.now().isoformat()
                    self.progress.total_time_spent += tutorial.estimated_time

                # Check for new badges
                new_badges = BadgeSystem.check_earned_badges(self.progress)
                for badge in new_badges:
                    self.progress.badges.append(badge)
                    print(f"\n🎉 Badge Earned: {badge.icon} {badge.name}!")
                    print(f"   {badge.description}\n")

                self.save()
                return

    def complete_tutorial(self, tutorial_id: str):
        """Mark an entire tutorial as completed"""
        if not self.progress:
            return

        for tutorial in self.progress.tutorials:
            if tutorial.tutorial_id == tutorial_id:
                for section in tutorial.sections:
                    if not section.completed:
                        section.completed = True
                        section.completed_at = datetime.now().isoformat()

                tutorial.completed = True
                tutorial.completed_at = datetime.now().isoformat()
                self.progress.total_time_spent += tutorial.estimated_time

                # Check for new badges
                new_badges = BadgeSystem.check_earned_badges(self.progress)
                for badge in new_badges:
                    self.progress.badges.append(badge)
                    print(f"\n🎉 Badge Earned: {badge.icon} {badge.name}!")
                    print(f"   {badge.description}\n")

                self.save()
                return

    def display_status(self):
        """Display current progress status"""
        if not self.progress:
            print("No progress data found. Run with --init to start tracking.")
            return

        print("\n" + "="*80)
        print(f"📚 AISHELL TUTORIAL PROGRESS - {self.progress.user_name}")
        print("="*80)

        # Overall stats
        overall = self.progress.overall_completion()
        completed_count = sum(1 for t in self.progress.tutorials if t.completed)
        total_count = len(self.progress.tutorials)

        print(f"\n📊 Overall Progress: {overall:.1f}% ({completed_count}/{total_count} tutorials)")
        print(f"⏱️  Total Time: {self.progress.total_time_spent} minutes")
        print(f"🔥 Current Streak: {self.progress.streak_days} days")
        print(f"🏅 Badges Earned: {len([b for b in self.progress.badges if b.earned_at])}/{len(BadgeSystem.get_all_badges())}")

        # Tutorial progress
        print("\n" + "-"*80)
        print("TUTORIAL PROGRESS")
        print("-"*80)

        for tutorial in self.progress.tutorials:
            completion = tutorial.completion_percentage()
            status = "✓" if tutorial.completed else "○"
            level_icon = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}[tutorial.level]

            print(f"\n{status} Tutorial {tutorial.tutorial_id}: {tutorial.tutorial_name} {level_icon}")
            print(f"   Progress: {completion:.0f}% | Time: {tutorial.estimated_time}min")

            if tutorial.sections and completion < 100:
                incomplete = [s for s in tutorial.sections if not s.completed]
                if incomplete:
                    print(f"   Next: {incomplete[0].section_name}")

        # Badges
        earned_badges = [b for b in self.progress.badges if b.earned_at]
        if earned_badges:
            print("\n" + "-"*80)
            print("BADGES EARNED")
            print("-"*80)
            for badge in earned_badges:
                print(f"{badge.icon} {badge.name} {badge.level.value}")
                print(f"   {badge.description}")

        # Next steps
        print("\n" + "-"*80)
        print("RECOMMENDED NEXT STEPS")
        print("-"*80)
        self._print_recommendations()

        print("\n" + "="*80 + "\n")

    def generate_certificate(self):
        """Generate completion certificate"""
        if not self.progress:
            print("No progress data found.")
            return

        if self.progress.overall_completion() < 100:
            print(f"Complete all tutorials to earn your certificate! (Currently {self.progress.overall_completion():.0f}% complete)")
            return

        print("\n" + "="*80)
        print(" "*28 + "CERTIFICATE OF COMPLETION")
        print("="*80)
        print()
        print(" "*30 + "This certifies that")
        print()
        print(" "*25 + f"╔{'═'*30}╗")
        print(" "*25 + f"║ {self.progress.user_name.center(30)} ║")
        print(" "*25 + f"╚{'═'*30}╝")
        print()
        print(" "*18 + "has successfully completed the")
        print()
        print(" "*20 + "AIShell Tutorial Series")
        print()
        print(" "*15 + f"Demonstrating mastery of:")
        print(" "*15 + "• Health Check Systems")
        print(" "*15 + "• Custom Agent Development")
        print(" "*15 + "• Tool Registry Management")
        print(" "*15 + "• Safety & Approval Workflows")
        print(" "*15 + "• Production Deployment")
        print()
        print(" "*20 + f"Total Learning Time: {self.progress.total_time_spent} minutes")
        print(" "*20 + f"Badges Earned: {len([b for b in self.progress.badges if b.earned_at])}")
        print()
        print(" "*20 + f"Completed: {datetime.fromisoformat(self.progress.tutorials[-1].completed_at).strftime('%B %d, %Y')}")
        print()
        print("="*80)
        print()

    def _print_recommendations(self):
        """Print personalized recommendations"""
        if not self.progress:
            return

        incomplete_tutorials = [t for t in self.progress.tutorials if not t.completed]

        if not incomplete_tutorials:
            print("🎉 Congratulations! You've completed all tutorials!")
            print("   Consider contributing your own tutorial or building a production system!")
            return

        # Find next tutorial based on prerequisites
        for tutorial in incomplete_tutorials:
            prereqs_met = all(
                any(t.tutorial_id == prereq_id and t.completed for t in self.progress.tutorials)
                for prereq_id in tutorial.prerequisites
            )

            if prereqs_met or not tutorial.prerequisites:
                print(f"📌 Next: Tutorial {tutorial.tutorial_id}: {tutorial.tutorial_name}")
                print(f"   Level: {tutorial.level.title()} | Time: {tutorial.estimated_time} minutes")

                if tutorial.sections:
                    incomplete_sections = [s for s in tutorial.sections if not s.completed]
                    if incomplete_sections:
                        print(f"   Resume at: {incomplete_sections[0].section_name}")
                break

    @staticmethod
    def _dict_to_tutorial(data: Dict) -> Tutorial:
        """Convert dict to Tutorial object"""
        sections = [ProgressTracker._dict_to_section(s) for s in data.get('sections', [])]
        return Tutorial(
            tutorial_id=data['tutorial_id'],
            tutorial_name=data['tutorial_name'],
            level=data['level'],
            estimated_time=data['estimated_time'],
            prerequisites=data.get('prerequisites', []),
            sections=sections,
            completed=data.get('completed', False),
            completed_at=data.get('completed_at')
        )

    @staticmethod
    def _dict_to_section(data: Dict) -> TutorialSection:
        """Convert dict to TutorialSection object"""
        return TutorialSection(
            section_id=data['section_id'],
            section_name=data['section_name'],
            description=data['description'],
            completed=data.get('completed', False),
            completed_at=data.get('completed_at'),
            notes=data.get('notes', '')
        )

    @staticmethod
    def _dict_to_badge(data: Dict) -> Badge:
        """Convert dict to Badge object"""
        # Parse level value (e.g., "🥉 Bronze" -> BadgeLevel.BRONZE)
        level_str = data['level'].split()[-1].upper()  # Get last word in uppercase
        level = BadgeLevel[level_str]

        return Badge(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            level=level,
            icon=data['icon'],
            earned_at=data.get('earned_at')
        )


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Track progress through AIShell tutorials")
    parser.add_argument(
        '--init',
        type=str,
        metavar='NAME',
        help='Initialize new progress tracker with your name'
    )
    parser.add_argument(
        '--complete',
        type=str,
        metavar='TUTORIAL_ID',
        help='Mark a tutorial as completed (e.g., 01, 02)'
    )
    parser.add_argument(
        '--section',
        type=str,
        metavar='SECTION_ID',
        help='Mark a specific section as completed (e.g., 01-1, 02-3)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Display current progress'
    )
    parser.add_argument(
        '--certificate',
        action='store_true',
        help='Generate completion certificate (if eligible)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset all progress (use with caution!)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Custom progress file location'
    )

    args = parser.parse_args()

    # Create tracker
    tracker = ProgressTracker(progress_file=args.file)

    # Handle commands
    if args.reset:
        if os.path.exists(tracker.progress_file):
            os.remove(tracker.progress_file)
            print("Progress reset successfully.")
        else:
            print("No progress file found.")
        return

    if args.init:
        tracker.initialize(user_name=args.init)
        tracker.save()
        print(f"Progress tracking initialized for {args.init}!")
        print(f"Progress saved to: {tracker.progress_file}")
        tracker.display_status()
        return

    # Load existing progress
    if not tracker.load():
        print("No progress found. Run with --init <your_name> to start tracking.")
        return

    if args.complete:
        tracker.complete_tutorial(args.complete)
        print(f"✓ Tutorial {args.complete} marked as completed!")
        tracker.display_status()

    elif args.section:
        # Parse section ID (e.g., "01-1" -> tutorial_id="01", section_id="01-1")
        tutorial_id = args.section.split('-')[0]
        tracker.complete_section(tutorial_id, args.section)
        print(f"✓ Section {args.section} marked as completed!")
        tracker.display_status()

    elif args.certificate:
        tracker.generate_certificate()

    else:
        # Default: show status
        tracker.display_status()


if __name__ == "__main__":
    main()
