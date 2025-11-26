#!/usr/bin/env python3
"""
CV Analysis Tool - Main Script
Analyzes multiple CVs against a job description and returns top 10 matches
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
import logging
from datetime import datetime

# Import our custom modules
from ai_gguf import GGUFModelRunner, load_config
from pdf_extractor import PDFTextExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CVAnalyzer:
    """Main class for CV analysis workflow"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the CV analyzer with AI model"""
        logger.info("Initializing CV Analyzer...")
        self.config = load_config(config_path)
        self.ai_runner = GGUFModelRunner(self.config)
        self.ai_runner.load_model()
        logger.info("AI model loaded successfully!")
    
    def get_cv_files(self, cv_directory: str) -> List[Path]:
        """
        Get all PDF files from the CV directory
        
        Args:
            cv_directory: Path to directory containing CV PDFs
            
        Returns:
            List of unique PDF file paths
        """
        cv_path = Path(cv_directory)
        
        if not cv_path.exists():
            raise FileNotFoundError(f"CV directory not found: {cv_directory}")
        
        if not cv_path.is_dir():
            raise ValueError(f"Path is not a directory: {cv_directory}")
        
        # Find all PDF files using case-insensitive pattern
        # Use a set to avoid duplicates on case-insensitive file systems
        pdf_files_set = set()
        
        # Method 1: Use case-insensitive glob pattern
        for pattern in ['*.pdf', '*.PDF', '*.Pdf']:
            for file in cv_path.glob(pattern):
                # Use resolve() to get absolute path and avoid duplicates
                pdf_files_set.add(file.resolve())
        
        # Convert set back to list and sort for consistent ordering
        pdf_files = sorted(list(pdf_files_set))
        
        if not pdf_files:
            raise ValueError(f"No PDF files found in directory: {cv_directory}")
        
        logger.info(f"Found {len(pdf_files)} unique PDF files")
        return pdf_files
    
    def extract_cv_text(self, pdf_path: Path) -> str:
        """
        Extract text from a CV PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            extractor = PDFTextExtractor(str(pdf_path))
            if extractor.extract():
                return extractor.get_text()
            else:
                logger.warning(f"Failed to extract text from {pdf_path.name}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path.name}: {e}")
            return ""
    
    def analyze_cv_match(self, cv_text: str, job_description: str, cv_name: str) -> Dict:
        """
        Use AI to analyze how well a CV matches the job description
        
        Args:
            cv_text: Extracted text from CV
            job_description: Job description text
            cv_name: Name of the CV file (for logging)
            
        Returns:
            Dictionary with analysis results including score and reasoning
        """
        logger.info(f"Analyzing CV: {cv_name}")
        
        # Create a comprehensive prompt for CV analysis
        prompt = f"""You are an objective CV evaluator. Compare the CV only against the job description. Be neutral, literal, and fully evidence-based.

HARD RULES

Use ONLY text explicitly present in the CV or JD. No assumptions, no invented experience.

Credit transferable skills ONLY when backed by a direct CV quote and label them “transferable”.

If a required skill is missing or unclear, mark “Insufficient evidence” and award zero points.

Do not infer or mention protected attributes.

Ambiguous CV claims must be marked “ambiguous” and penalized.

OUTPUT FORMAT (exact order, plain text)

OVERALL SUMMARY:
1–2 sentences only.

KEY STRENGTHS:

Bullet points with a short CV quote in parentheses as EVIDENCE.

POTENTIAL GAPS:

Bullet points with either a CV quote or “Insufficient evidence”.

FIT SCORE:
Fit Score: X%

SCORE BREAKDOWN:

Bullet list of exact rubric adjustments used.

End with one short justification sentence.

RECOMMENDATION:
SHORTLIST / REVIEW / REJECT

NOTE:
State any ambiguity in one short line.

SCORING RUBRIC (deterministic)

Start at 50.

Add:
+15 each required skill explicitly present (max +45)
+10 each strong project proving a required responsibility (max +20)
+5 each deployment/production evidence (max +10)
+5 each preferred skill (max +10)
+5 each transferable skill with explicit quote (max +10)

Subtract:
-20 each missing required skill
-10 each contradictory claim
-5 each ambiguous or weak evidence

Clamp final score to 0–100.

THRESHOLDS

≥75 SHORTLIST
60–74 REVIEW
<60 REJECT

EXTRA RULES

Always quote CV text for every claim.

Personal adjectives without proof get “Insufficient evidence”.

If JD has unclear or missing requirements, output: Insufficient job description clarity.

Job Description:
{job_description}

CV Content:
{cv_text}
"""
        
        try:
            # Use chat format for better structured responses
            messages = [
                {
                    "role": "system",
                    "content": "You are an objective technical recruiter AI. Follow all rules and formatting instructions precisely."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.ai_runner.chat(
                messages=messages,
                max_tokens=1024,
                temperature=0.2  # Lower temperature for deterministic output
            )
            
            # Parse the plain text response
            analysis = self._parse_analysis(response)
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing CV {cv_name}: {e}")
            return {
                "fit_score": 0,
                "recommendation": "ERROR",
                "summary": f"Error: {str(e)}",
                "strengths": [],
                "gaps": [],
                "breakdown": []
            }
    
    def _parse_analysis(self, response_text: str) -> Dict:
        """Parse the plain text AI response into a dictionary"""
        analysis = {}
        
        # Helper to extract a section
        def extract_section(start_key: str, end_key: str) -> str:
            try:
                start_index = response_text.index(start_key) + len(start_key)
                end_index = response_text.index(end_key, start_index)
                return response_text[start_index:end_index].strip()
            except ValueError:
                return ""
        
        # Helper to extract the final section
        def extract_final_section(start_key: str) -> str:
            try:
                start_index = response_text.index(start_key) + len(start_key)
                return response_text[start_index:].strip()
            except ValueError:
                return ""

        # Extract FIT SCORE
        score_match = re.search(r"Fit Score:\s*(\d+)%", response_text)
        analysis['fit_score'] = int(score_match.group(1)) if score_match else 0
        
        # Extract RECOMMENDATION
        rec_match = re.search(r"RECOMMENDATION:\s*(SHORTLIST|REVIEW|REJECT)", response_text)
        analysis['recommendation'] = rec_match.group(1) if rec_match else "N/A"

        # Extract sections using headers
        analysis['summary'] = extract_section("OVERALL SUMMARY:", "KEY STRENGTHS:").strip()
        strengths_text = extract_section("KEY STRENGTHS:", "POTENTIAL GAPS:")
        gaps_text = extract_section("POTENTIAL GAPS:", "FIT SCORE:")
        breakdown_text = extract_section("SCORE BREAKDOWN:", "RECOMMENDATION:")
        note_text = extract_final_section("NOTE:")

        # Parse bulleted lists
        analysis['strengths'] = [s.strip() for s in strengths_text.split('- ') if s.strip()]
        analysis['gaps'] = [g.strip() for g in gaps_text.split('- ') if g.strip()]
        analysis['breakdown'] = [b.strip() for b in breakdown_text.split('- ') if b.strip()]
        analysis['note'] = note_text.strip()

        return analysis

    def process_all_cvs(self, cv_directory: str, job_description: str) -> List[Dict]:
        """
        Process all CVs in the directory and analyze them
        
        Args:
            cv_directory: Path to directory containing CVs
            job_description: Job description text
            
        Returns:
            List of analysis results for each CV
        """
        cv_files = self.get_cv_files(cv_directory)
        results = []
        processed_files = set()  # Track processed files to avoid duplicates
        
        logger.info(f"Processing {len(cv_files)} CVs...")
        print(f"\n{'='*60}")
        print(f"Processing {len(cv_files)} CVs against job description")
        print(f"{'='*60}\n")
        
        for idx, cv_file in enumerate(cv_files, 1):
            # Double-check we haven't processed this file
            file_key = str(cv_file.resolve())
            if file_key in processed_files:
                logger.warning(f"Skipping duplicate file: {cv_file.name}")
                continue
            
            processed_files.add(file_key)
            
            print(f"[{idx}/{len(cv_files)}] Processing: {cv_file.name}")
            
            # Extract text
            cv_text = self.extract_cv_text(cv_file)
            
            if not cv_text or len(cv_text.strip()) < 50:
                logger.warning(f"Skipping {cv_file.name} - insufficient text extracted")
                print(f"  ⚠ Warning: Could not extract sufficient text from {cv_file.name}")
                continue
            
            # Analyze with AI
            analysis = self.analyze_cv_match(cv_text, job_description, cv_file.name)
            
            # Add CV file info to results
            result = {
                "cv_file": cv_file.name,
                "cv_path": str(cv_file),
                "fit_score": analysis.get("fit_score", 0),
                "recommendation": analysis.get("recommendation", "N/A"),
                "summary": analysis.get("summary", ""),
                "strengths": analysis.get("strengths", []),
                "gaps": analysis.get("gaps", []),
                "breakdown": analysis.get("breakdown", []),
                "note": analysis.get("note", ""),
                "cv_text_preview": cv_text[:500]  # Store preview for reference
            }
            
            results.append(result)
            print(f"  ✓ Recommendation: {result['recommendation']} (Score: {result['fit_score']}/100)\n")
        
        logger.info(f"Successfully processed {len(results)} unique CVs")
        return results
    
    def get_top_candidates(self, results: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Get top N candidates sorted by match score
        
        Args:
            results: List of analysis results
            top_n: Number of top candidates to return
            
        Returns:
            Sorted list of top candidates
        """
        # Sort by fit score (descending)
        sorted_results = sorted(results, key=lambda x: x['fit_score'], reverse=True)
        return sorted_results[:top_n]
    
    def display_results(self, top_candidates: List[Dict], job_description: str):
        """
        Display the top candidates in a formatted way
        
        Args:
            top_candidates: List of top candidate results
            job_description: Job description (for reference)
        """
        print("\n" + "="*80)
        print("TOP 10 CANDIDATES - CV ANALYSIS RESULTS")
        print("="*80)
        print(f"\nJob Description Preview: {job_description[:200]}...")
        print(f"\nTotal Candidates Analyzed: {len(top_candidates)}")
        print("\n" + "-"*80 + "\n")
        
        for rank, candidate in enumerate(top_candidates, 1):
            print(f"RANK #{rank}")
            print(f"CV File: {candidate['cv_file']}")
            print(f"Fit Score: {candidate['fit_score']}/100")
            print(f"Recommendation: {candidate['recommendation']}")
            print(f"\nSummary: {candidate.get('summary', 'N/A')}")
            
            print(f"\nKey Strengths:")
            for strength in candidate.get('strengths', []):
                print(f"  - {strength}")
            
            print(f"\nPotential Gaps:")
            for gap in candidate.get('gaps', []):
                print(f"  - {gap}")

            if candidate.get('breakdown'):
                print(f"\nScore Breakdown:")
                for item in candidate.get('breakdown', []):
                    print(f"  - {item}")
            
            if candidate.get('note'):
                print(f"\nNote: {candidate.get('note')}")

            print(f"\nCV Preview: {candidate.get('cv_text_preview', '')[:200]}...")
            print("\n" + "-"*80 + "\n")
    
    def save_results(self, top_candidates: List[Dict], output_file: str = None):
        """
        Save results to a JSON file
        
        Args:
            top_candidates: List of top candidate results
            output_file: Output file path (optional, defaults to script directory with timestamp)
        """
        if not output_file:
            # Get the directory where the script is located
            script_dir = Path(__file__).parent.resolve()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = script_dir / f"cv_analysis_results_{timestamp}.json"
        else:
            output_file = Path(output_file)
        
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "total_candidates": len(top_candidates),
            "candidates": top_candidates
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_file}")
        print(f"\n✓ Results saved to: {output_file}")
        
        return str(output_file)


def main():
    """Main execution function"""
    try:
        # Get user inputs
        cv_directory, job_description = get_user_inputs()
        
        # Initialize analyzer
        print("\n" + "="*60)
        print("Initializing AI Model...")
        print("="*60)
        analyzer = CVAnalyzer()
        
        # Process all CVs
        all_results = analyzer.process_all_cvs(cv_directory, job_description)
        
        if not all_results:
            print("\n⚠ No CVs were successfully analyzed!")
            sys.exit(1)
        
        # Get top 10 candidates
        top_candidates = analyzer.get_top_candidates(all_results, top_n=10)
        
        # Display results
        analyzer.display_results(top_candidates, job_description)
        
        # Save results automatically to script directory
        output_path = analyzer.save_results(top_candidates)
        
        print("\n" + "="*60)
        print("Analysis Complete!")
        print(f"Results saved to: {output_path}")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)
