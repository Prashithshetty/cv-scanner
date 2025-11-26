#!/usr/bin/env python3
"""
CV Analysis Tool - Main Script (Optimized)
Analyzes multiple CVs against a job description using:
- JSON-based AI extraction
- Python deterministic scoring
- GPU batch processing
- Parallel text extraction
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import our custom modules
from ai_gguf import GGUFModelRunner, load_config
from pdf_extractor import PDFTextExtractor
from scorer import CVScorer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CVAnalyzer:
    """Main class for CV analysis workflow with optimizations"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the CV analyzer with AI model and scorer"""
        logger.info("Initializing CV Analyzer...")
        self.config = load_config(config_path)
        self.ai_runner = GGUFModelRunner(self.config)
        self.ai_runner.load_model()
        self.scorer = CVScorer()
        logger.info("AI model and scorer loaded successfully!")
    
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
        pdf_files_set = set()
        
        for pattern in ['*.pdf', '*.PDF', '*.Pdf']:
            for file in cv_path.glob(pattern):
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
    
    def extract_cvs_parallel(self, cv_files: List[Path], max_workers: int = 4) -> Dict[str, str]:
        """
        Extract text from multiple CVs in parallel
        
        Args:
            cv_files: List of CV file paths
            max_workers: Number of parallel workers
            
        Returns:
            Dictionary mapping cv_name to extracted text
        """
        logger.info(f"Extracting text from {len(cv_files)} CVs in parallel...")
        cv_texts = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all extraction tasks
            future_to_cv = {
                executor.submit(self.extract_cv_text, cv_file): cv_file 
                for cv_file in cv_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_cv):
                cv_file = future_to_cv[future]
                try:
                    text = future.result()
                    if text and len(text.strip()) >= 50:
                        cv_texts[cv_file.name] = text
                    else:
                        logger.warning(f"Insufficient text from {cv_file.name}")
                except Exception as e:
                    logger.error(f"Failed to extract {cv_file.name}: {e}")
        
        logger.info(f"Successfully extracted {len(cv_texts)} CVs")
        return cv_texts
    
    def parse_job_requirements(self, job_description: str) -> Dict:
        """
        Parse job description into structured requirements
        This helps the AI understand what to look for
        
        Args:
            job_description: Raw job description text
            
        Returns:
            Structured requirements dictionary
        """
        # For now, return as-is. You can enhance this to parse JD into sections
        return {
            "full_text": job_description,
            "note": "AI will extract relevant skills and requirements from this description"
        }
    
    def extract_cv_data(self, cv_text: str, job_description: str, cv_name: str) -> Dict:
        """
        Use AI to extract structured data from CV (NOT calculate scores)
        
        Args:
            cv_text: Extracted text from CV
            job_description: Job description text
            cv_name: Name of the CV file (for logging)
            
        Returns:
            Dictionary with extracted structured data
        """
        logger.info(f"Extracting data from CV: {cv_name}")
        
        # Create JSON extraction prompt
        prompt = f"""You are a data extraction AI. Extract ONLY factual information from the CV in JSON format.

CRITICAL RULES:
1. Output ONLY valid JSON (no extra text, no markdown)
2. Quote exact CV text as evidence (max 100 chars per quote)
3. Do NOT calculate scores or make recommendations
4. If evidence is unclear, set found=false
5. Be objective and literal

Job Description:
{job_description}

CV Content:
{cv_text[:3000]}

OUTPUT FORMAT (valid JSON only):
{{
  "required_skills": [
    {{"skill": "skill name from JD", "found": true/false, "evidence": "exact CV quote or null"}}
  ],
  "preferred_skills": [
    {{"skill": "skill name from JD", "found": true/false, "evidence": "exact CV quote or null"}}
  ],
  "projects": [
    {{
      "title": "project name",
      "technologies": ["tech1", "tech2"],
      "deployment_proof": true/false,
      "relevance": "high/medium/low"
    }}
  ],
  "transferable_skills": [
    {{"skill": "skill name", "evidence": "exact CV quote"}}
  ],
  "experience_years": number,
  "issues": [
    {{"type": "ambiguous/contradiction/weak_evidence", "description": "brief note"}}
  ]
}}

Extract data now (JSON only):"""
        
        try:
            # Use chat format for better structured responses
            messages = [
                {
                    "role": "system",
                    "content": "You are a precise data extraction AI. Output only valid JSON with no extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.ai_runner.chat(
                messages=messages,
                max_tokens=1024,
                temperature=0.3,  # Low for consistency
                stream=False
            )
            
            # Parse JSON response
            extracted_data = self._parse_json_response(response)
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting data from CV {cv_name}: {e}")
            return self._get_empty_extraction()
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse AI JSON response with error handling"""
        try:
            # Try to find JSON in response
            # Sometimes the AI might add extra text, so we extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                return data
            else:
                logger.warning("No JSON found in AI response")
                return self._get_empty_extraction()
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Response was: {response[:200]}")
            return self._get_empty_extraction()
    
    def _get_empty_extraction(self) -> Dict:
        """Return empty extraction structure"""
        return {
            "required_skills": [],
            "preferred_skills": [],
            "projects": [],
            "transferable_skills": [],
            "experience_years": 0,
            "issues": [{"type": "error", "description": "Failed to extract data"}]
        }
    
    def generate_summary(self, extracted_data: Dict, score_result: Dict, cv_name: str) -> str:
        """
        Generate a human-readable summary using AI (optional second pass)
        
        Args:
            extracted_data: Data extracted by AI
            score_result: Scoring results from Python
            cv_name: CV file name
            
        Returns:
            Summary text
        """
        try:
            prompt = f"""Generate a brief 2-3 sentence hiring summary.

Candidate: {cv_name}
Score: {score_result['final_score']}/100
Recommendation: {score_result['recommendation']}

Key Points:
- Required skills found: {sum(1 for s in extracted_data.get('required_skills', []) if s.get('found'))}
- Projects: {len(extracted_data.get('projects', []))}
- Issues: {len(extracted_data.get('issues', []))}

Write a concise summary explaining this candidate's fit:"""
            
            messages = [
                {"role": "system", "content": "You are a concise hiring analyst."},
                {"role": "user", "content": prompt}
            ]
            
            summary = self.ai_runner.chat(
                messages=messages,
                max_tokens=150,
                temperature=0.5,
                stream=False
            )
            
            return summary.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Summary generation failed"
    
    def process_all_cvs(self, cv_directory: str, job_description: str, batch_size: int = 4) -> List[Dict]:
        """
        Process all CVs in the directory and analyze them
        
        Args:
            cv_directory: Path to directory containing CVs
            job_description: Job description text
            batch_size: Number of CVs to process in each batch
            
        Returns:
            List of analysis results for each CV
        """
        # Step 1: Get all CV files
        cv_files = self.get_cv_files(cv_directory)
        
        # Step 2: Extract text in parallel
        print(f"\n{'='*60}")
        print(f"Extracting text from {len(cv_files)} CVs...")
        print(f"{'='*60}\n")
        cv_texts = self.extract_cvs_parallel(cv_files, max_workers=4)
        
        if not cv_texts:
            logger.error("No CVs with sufficient text found!")
            return []
        
        # Step 3: Process CVs
        results = []
        cv_items = list(cv_texts.items())
        
        logger.info(f"Processing {len(cv_items)} CVs in batches of {batch_size}...")
        print(f"\n{'='*60}")
        print(f"Analyzing {len(cv_items)} CVs against job description")
        print(f"{'='*60}\n")
        
        for idx, (cv_name, cv_text) in enumerate(cv_items, 1):
            print(f"[{idx}/{len(cv_items)}] Processing: {cv_name}")
            
            # Extract data with AI
            extracted_data = self.extract_cv_data(cv_text, job_description, cv_name)
            
            # Calculate score with Python
            score_result = self.scorer.calculate_score(extracted_data)
            
            # Optional: Generate summary
            summary = self.generate_summary(extracted_data, score_result, cv_name)
            
            # Compile result
            result = {
                "cv_file": cv_name,
                "fit_score": score_result['final_score'],
                "recommendation": score_result['recommendation'],
                "summary": summary,
                "breakdown": score_result['breakdown'],
                "extracted_data": extracted_data,
                "details": score_result.get('details', {}),
                "cv_text_preview": cv_text[:500]
            }
            
            results.append(result)
            print(f"  ✓ Score: {result['fit_score']}/100 | {result['recommendation']}\n")
        
        logger.info(f"Successfully processed {len(results)} CVs")
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
            
            print(f"\nScore Breakdown:")
            for item in candidate.get('breakdown', []):
                print(f"  {item}")
            
            # Show extracted data highlights
            extracted = candidate.get('extracted_data', {})
            req_skills = [s for s in extracted.get('required_skills', []) if s.get('found')]
            if req_skills:
                print(f"\nRequired Skills Found ({len(req_skills)}):")
                for skill in req_skills[:5]:  # Show first 5
                    print(f"  ✓ {skill['skill']}")
            
            projects = extracted.get('projects', [])
            if projects:
                print(f"\nRelevant Projects ({len(projects)}):")
                for proj in projects[:3]:  # Show first 3
                    print(f"  • {proj.get('title', 'Unnamed')} ({proj.get('relevance', 'N/A')})")
            
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


def get_user_inputs() -> Tuple[str, str]:
    """Get CV directory and job description from user"""
    print("\n" + "="*60)
    print("CV Analysis Tool - Enhanced with GPU Optimization")
    print("="*60 + "\n")
    
    # Get CV directory
    cv_directory = input("Enter the path to CV directory (or press Enter for 'fake_cvs'): ").strip()
    if not cv_directory:
        cv_directory = "fake_cvs"
    
    # Get job description
    print("\nEnter job description (type 'END' on a new line when done):")
    job_lines = []
    while True:
        line = input()
        if line.strip() == 'END':
            break
        job_lines.append(line)
    
    job_description = '\n'.join(job_lines)
    
    if not job_description.strip():
        raise ValueError("Job description cannot be empty!")
    
    return cv_directory, job_description


def main():
    """Main execution function"""
    try:
        # Get user inputs
        cv_directory, job_description = get_user_inputs()
        
        # Initialize analyzer
        print("\n" + "="*60)
        print("Initializing AI Model and Scoring Engine...")
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


if __name__ == "__main__":
    main()
