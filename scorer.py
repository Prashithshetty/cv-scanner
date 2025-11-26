#!/usr/bin/env python3
"""
Deterministic CV Scoring Engine
Calculates scores based on AI-extracted data using Python logic
"""

import json
import logging
from typing import Dict, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class CVScorer:
    """
    Deterministic scoring engine that calculates CV match scores
    based on structured data extracted by AI
    """
    
    def __init__(self, rules_path: str = None):
        """
        Initialize the scorer with scoring rules
        
        Args:
            rules_path: Optional path to custom scoring rules JSON file
        """
        self.rules = self._load_rules(rules_path)
        logger.info("CVScorer initialized with scoring rules")
    
    def _load_rules(self, rules_path: str = None) -> Dict:
        """Load scoring rules from file or use defaults"""
        default_rules = {
            'base_score': 50,
            'additions': {
                'required_skill': {'points': 15, 'max_count': 3, 'max_points': 45},
                'preferred_skill': {'points': 5, 'max_count': 2, 'max_points': 10},
                'relevant_project': {'points': 10, 'max_count': 2, 'max_points': 20},
                'deployment_proof': {'points': 5, 'max_count': 2, 'max_points': 10},
                'transferable_skill': {'points': 5, 'max_count': 2, 'max_points': 10}
            },
            'deductions': {
                'missing_required': -20,
                'contradiction': -10,
                'ambiguous': -5,
                'weak_evidence': -3
            },
            'thresholds': {
                'shortlist': 75,
                'review': 60
            }
        }
        
        if rules_path and Path(rules_path).exists():
            logger.info(f"Loading custom scoring rules from {rules_path}")
            with open(rules_path, 'r') as f:
                custom_rules = json.load(f)
                default_rules.update(custom_rules)
        
        return default_rules
    
    def calculate_score(self, extracted_data: Dict) -> Dict:
        """
        Calculate final score from AI-extracted data
        
        Args:
            extracted_data: Structured data extracted by AI containing:
                - required_skills: List of {skill, found, evidence}
                - preferred_skills: List of {skill, found, evidence}
                - projects: List of {title, technologies, deployment_proof, relevance}
                - transferable_skills: List of {skill, evidence}
                - issues: List of {type, description}
        
        Returns:
            Dictionary containing:
                - final_score: Integer score (0-100)
                - breakdown: List of scoring steps with explanations
                - recommendation: SHORTLIST/REVIEW/REJECT
                - details: Detailed scoring information
        """
        score = self.rules['base_score']
        breakdown = [f"Base score: {score}"]
        details = {}
        
        # 1. Required Skills
        required_score, required_breakdown = self._score_required_skills(
            extracted_data.get('required_skills', [])
        )
        score += required_score
        breakdown.extend(required_breakdown)
        details['required_skills'] = required_breakdown
        
        # 2. Preferred Skills
        preferred_score, preferred_breakdown = self._score_preferred_skills(
            extracted_data.get('preferred_skills', [])
        )
        score += preferred_score
        breakdown.extend(preferred_breakdown)
        details['preferred_skills'] = preferred_breakdown
        
        # 3. Projects
        projects_score, projects_breakdown = self._score_projects(
            extracted_data.get('projects', [])
        )
        score += projects_score
        breakdown.extend(projects_breakdown)
        details['projects'] = projects_breakdown
        
        # 4. Transferable Skills
        transfer_score, transfer_breakdown = self._score_transferable_skills(
            extracted_data.get('transferable_skills', [])
        )
        score += transfer_score
        breakdown.extend(transfer_breakdown)
        details['transferable_skills'] = transfer_breakdown
        
        # 5. Issues (Deductions)
        issues_score, issues_breakdown = self._score_issues(
            extracted_data.get('issues', [])
        )
        score += issues_score  # This will be negative
        breakdown.extend(issues_breakdown)
        details['issues'] = issues_breakdown
        
        # Clamp score to 0-100
        score = max(0, min(100, score))
        
        # Determine recommendation
        recommendation = self._get_recommendation(score)
        
        return {
            'final_score': score,
            'breakdown': breakdown,
            'recommendation': recommendation,
            'details': details
        }
    
    def _score_required_skills(self, required_skills: List[Dict]) -> Tuple[int, List[str]]:
        """Score required skills section"""
        found_skills = [s for s in required_skills if s.get('found', False)]
        missing_skills = [s for s in required_skills if not s.get('found', False)]
        
        rules = self.rules['additions']['required_skill']
        points_per_skill = rules['points']
        max_points = rules['max_points']
        
        # Points for found skills
        found_count = len(found_skills)
        points = min(found_count * points_per_skill, max_points)
        
        breakdown = []
        if found_count > 0:
            breakdown.append(f"+{points} for {found_count} required skill(s) found")
            for skill in found_skills[:3]:  # Show first 3
                breakdown.append(f"  ✓ {skill['skill']}: \"{skill.get('evidence', 'N/A')[:60]}...\"")
        
        # Deductions for missing skills
        missing_penalty = len(missing_skills) * self.rules['deductions']['missing_required']
        if missing_skills:
            breakdown.append(f"{missing_penalty} for {len(missing_skills)} missing required skill(s)")
            for skill in missing_skills[:3]:  # Show first 3
                breakdown.append(f"  ✗ Missing: {skill['skill']}")
        
        total_score = points + missing_penalty
        return total_score, breakdown
    
    def _score_preferred_skills(self, preferred_skills: List[Dict]) -> Tuple[int, List[str]]:
        """Score preferred skills section"""
        found_skills = [s for s in preferred_skills if s.get('found', False)]
        
        rules = self.rules['additions']['preferred_skill']
        points_per_skill = rules['points']
        max_count = rules['max_count']
        
        count = min(len(found_skills), max_count)
        points = count * points_per_skill
        
        breakdown = []
        if count > 0:
            breakdown.append(f"+{points} for {count} preferred skill(s)")
            for skill in found_skills[:max_count]:
                breakdown.append(f"  ✓ {skill['skill']}")
        
        return points, breakdown
    
    def _score_projects(self, projects: List[Dict]) -> Tuple[int, List[str]]:
        """Score projects and deployment proof"""
        relevant_projects = [p for p in projects if p.get('relevance') in ['high', 'medium']]
        high_relevance = [p for p in projects if p.get('relevance') == 'high']
        deployment_proofs = [p for p in projects if p.get('deployment_proof', False)]
        
        # Project relevance points
        proj_rules = self.rules['additions']['relevant_project']
        proj_count = min(len(high_relevance), proj_rules['max_count'])
        proj_points = proj_count * proj_rules['points']
        
        # Deployment proof points
        deploy_rules = self.rules['additions']['deployment_proof']
        deploy_count = min(len(deployment_proofs), deploy_rules['max_count'])
        deploy_points = deploy_count * deploy_rules['points']
        
        total_points = proj_points + deploy_points
        
        breakdown = []
        if proj_points > 0:
            breakdown.append(f"+{proj_points} for {proj_count} highly relevant project(s)")
            for proj in high_relevance[:proj_rules['max_count']]:
                breakdown.append(f"  ✓ {proj.get('title', 'Unnamed project')}")
        
        if deploy_points > 0:
            breakdown.append(f"+{deploy_points} for {deploy_count} deployment proof(s)")
        
        return total_points, breakdown
    
    def _score_transferable_skills(self, transferable_skills: List[Dict]) -> Tuple[int, List[str]]:
        """Score transferable skills"""
        rules = self.rules['additions']['transferable_skill']
        count = min(len(transferable_skills), rules['max_count'])
        points = count * rules['points']
        
        breakdown = []
        if count > 0:
            breakdown.append(f"+{points} for {count} transferable skill(s)")
            for skill in transferable_skills[:rules['max_count']]:
                breakdown.append(f"  ✓ {skill.get('skill', 'N/A')}")
        
        return points, breakdown
    
    def _score_issues(self, issues: List[Dict]) -> Tuple[int, List[str]]:
        """Score issues (deductions)"""
        total_penalty = 0
        breakdown = []
        
        for issue in issues:
            issue_type = issue.get('type', 'ambiguous')
            penalty = self.rules['deductions'].get(issue_type, -5)
            total_penalty += penalty
            breakdown.append(f"{penalty} for {issue_type}: {issue.get('description', 'N/A')[:60]}")
        
        return total_penalty, breakdown
    
    def _get_recommendation(self, score: int) -> str:
        """Determine recommendation based on score"""
        if score >= self.rules['thresholds']['shortlist']:
            return 'SHORTLIST'
        elif score >= self.rules['thresholds']['review']:
            return 'REVIEW'
        else:
            return 'REJECT'
    
    def save_rules(self, filepath: str):
        """Save current scoring rules to a JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.rules, f, indent=2)
        logger.info(f"Scoring rules saved to {filepath}")


def create_default_rules_file(filepath: str = "scoring_rules.json"):
    """Create a default scoring rules file for customization"""
    scorer = CVScorer()
    scorer.save_rules(filepath)
    print(f"Default scoring rules saved to {filepath}")


if __name__ == "__main__":
    # Create a default rules file
    create_default_rules_file()
