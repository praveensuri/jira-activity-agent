"""JIRA API connector for activity tracking."""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from jira import JIRA
from config import Config

logger = logging.getLogger(__name__)


class JIRAConnector:
    """Manages JIRA API connections and queries."""

    def __init__(self):
        """Initialize JIRA connector with credentials from config."""
        self.jira_url = Config.JIRA_URL
        self.username = Config.JIRA_USERNAME
        self.api_token = Config.JIRA_API_TOKEN
        self.project_key = Config.JIRA_PROJECT_KEY

        self.client = self._connect()

    def _connect(self) -> JIRA:
        """Establish connection to JIRA."""
        try:
            jira = JIRA(
                server=self.jira_url,
                basic_auth=(self.username, self.api_token),
                options={"verify": True, "timeout": 30},
            )
            logger.info(f"Connected to JIRA: {self.jira_url}")
            return jira
        except Exception as e:
            logger.error(f"Failed to connect to JIRA: {e}")
            raise

    def get_all_stories(self, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all stories from the project."""
        max_results = max_results or Config.MAX_RESULTS
        jql = f'project = {self.project_key} ORDER BY created DESC'
        
        try:
            issues = self.client.search_issues(jql, maxResults=max_results)
            stories = []
            for issue in issues:
                stories.append({
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "created": issue.fields.created,
                    "updated": issue.fields.updated,
                    "assignee": issue.fields.assignee.name if issue.fields.assignee else None,
                })
            logger.info(f"Retrieved {len(stories)} stories from {self.project_key}")
            return stories
        except Exception as e:
            logger.error(f"Error retrieving stories: {e}")
            return []

    def get_story_details(self, story_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific story."""
        try:
            issue = self.client.issue(story_key)
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "assignee": issue.fields.assignee.name if issue.fields.assignee else None,
                "priority": issue.fields.priority.name if issue.fields.priority else None,
                "labels": issue.fields.labels,
            }
        except Exception as e:
            logger.error(f"Error retrieving story {story_key}: {e}")
            return None

    def get_story_changelog(self, story_key: str) -> List[Dict[str, Any]]:
        """Get changelog for a story (phase transitions and edits)."""
        try:
            issue = self.client.issue(story_key, expand="changelog")
            changelog = []
            
            for history in issue.changelog.histories:
                for item in history.items:
                    changelog.append({
                        "timestamp": history.created,
                        "author": history.author.name,
                        "field": item.field,
                        "from_value": item.fromString,
                        "to_value": item.toString,
                    })
            
            logger.info(f"Retrieved {len(changelog)} changelog entries for {story_key}")
            return changelog
        except Exception as e:
            logger.error(f"Error retrieving changelog for {story_key}: {e}")
            return []

    def get_story_comments(self, story_key: str) -> List[Dict[str, Any]]:
        """Get all comments on a story."""
        try:
            issue = self.client.issue(story_key)
            comments = []
            
            if issue.fields.comment.comments:
                for comment in issue.fields.comment.comments:
                    comments.append({
                        "author": comment.author.name,
                        "timestamp": comment.created,
                        "body": comment.body,
                    })
            
            logger.info(f"Retrieved {len(comments)} comments for {story_key}")
            return comments
        except Exception as e:
            logger.error(f"Error retrieving comments for {story_key}: {e}")
            return []

    def get_story_worklogs(self, story_key: str) -> List[Dict[str, Any]]:
        """Get work logs for a story (time tracking)."""
        try:
            issue = self.client.issue(story_key)
            worklogs = []
            
            if issue.fields.worklog.worklogs:
                for worklog in issue.fields.worklog.worklogs:
                    worklogs.append({
                        "author": worklog.author.name,
                        "timestamp": worklog.created,
                        "time_spent": worklog.timeSpent,
                        "time_spent_seconds": worklog.timeSpentSeconds,
                    })
            
            logger.info(f"Retrieved {len(worklogs)} worklogs for {story_key}")
            return worklogs
        except Exception as e:
            logger.error(f"Error retrieving worklogs for {story_key}: {e}")
            return []

    def get_transitions_for_issue(self, story_key: str) -> List[Dict[str, Any]]:
        """Get status transitions from changelog."""
        changelog = self.get_story_changelog(story_key)
        transitions = [entry for entry in changelog if entry["field"] == "status"]
        return transitions
