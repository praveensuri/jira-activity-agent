"""Data models for JIRA Activity Agent."""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class IssuePhase(str, Enum):
    """Issue phase/status constants."""
    BACKLOG = "Backlog"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"


@dataclass
class UserActivity:
    """User activity record."""
    user: str
    action: str
    timestamp: datetime
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class PhaseTransition:
    """Phase transition record."""
    from_phase: str
    to_phase: str
    timestamp: datetime
    user: str
    duration_in_phase: Optional[float] = None  # days

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class StoryActivity:
    """Complete story activity information."""
    story_key: str
    story_title: str
    current_phase: str
    created_at: datetime
    updated_at: datetime
    activities: List[UserActivity]
    phase_transitions: List[PhaseTransition]
    contributors: List[str]
    velocity_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "story_key": self.story_key,
            "story_title": self.story_title,
            "current_phase": self.current_phase,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "activities": [a.to_dict() for a in self.activities],
            "phase_transitions": [t.to_dict() for t in self.phase_transitions],
            "contributors": self.contributors,
            "velocity_score": self.velocity_score,
        }


@dataclass
class ActivityReport:
    """Activity report for a project."""
    project_key: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_stories: int
    total_activities: int
    stories_by_phase: Dict[str, int]
    top_contributors: List[tuple]  # (username, activity_count)
    phase_completion_times: Dict[str, float]  # phase: average days
    insights: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_key": self.project_key,
            "generated_at": self.generated_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_stories": self.total_stories,
            "total_activities": self.total_activities,
            "stories_by_phase": self.stories_by_phase,
            "top_contributors": self.top_contributors,
            "phase_completion_times": self.phase_completion_times,
            "insights": self.insights,
        }
