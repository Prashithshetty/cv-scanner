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
import threading

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
        
        # Performance settings
        self.parallel_workers = self.config.get('parallel_workers', 3)
        self.enable_summaries = self.config.get('enable_summaries', False)
        self.pdf_workers = self.config.get('pdf_extraction_workers', 4)
        
        # Thread safety for model access
        self.model_lock = threading.Lock()
        
        # Pre-compile regex patterns for performance
        self.json_block_pattern = re.compile(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```')
        self.json_fallback_pattern = re.compile(r'\{[\s\S]*\}')
        self.trailing_comma_pattern = re.compile(r',\s*([}\]])')
        self.missing_comma_obj_pattern = re.compile(r'(\})\s*(\{)')
        self.missing_comma_arr_pattern = re.compile(r'(\])\s*(\[)')
        self.skill_pattern = re.compile(r'"skill":\s*"([^"]+)".*?"found":\s*(true|false)', re.IGNORECASE)
        
        logger.info(f"AI model and scorer loaded successfully!")
        logger.info(f"Performance settings: parallel_workers={self.parallel_workers}, summaries={'ON' if self.enable_summaries else 'OFF'}")
    
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
        Extract text from a CV PDF file with early truncation
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content (truncated to 2500 chars)
        """
        try:
            extractor = PDFTextExtractor(str(pdf_path))
            if extractor.extract():
                full_text = extractor.get_text()
                # Early truncation to save memory (slightly more than needed for AI)
                return full_text[:2500]
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
        logger.info(f"Extracting text from {len(cv_files)} CVs in parallel (workers={max_workers})...")
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
        
        # Truncate CV text to avoid token limits (keep first 2000 chars for better accuracy)
        cv_text_truncated = cv_text[:2000]
        
        # Create a more concise and strict JSON extraction prompt
        prompt = f"""Extract CV data as valid JSON. NO markdown, NO extra text, NO assumptions.

Rules:
1. Mark a skill as "found": true ONLY if the CV text contains a direct substring match.  
2. Evidence MUST be an exact quote copied VERBATIM from CV Text. If no exact match exists, use null and set found: false.  
3. DO NOT infer, guess, or assume any skill or technology that is not literally present.  
4. Projects must ONLY use titles and technologies explicitly mentioned in the CV.  
5. "transferable_skills" must ONLY list skills with direct quotes from CV Text.  
6. "experience_years" must be 0 unless the CV explicitly states a number.  
7. "issues" should list missing required skills if they were not found.

Job Requirements:
{job_description[:800]}

CV Text:
{cv_text_truncated}

Output this EXACT JSON structure with NO additional text:
{{
  "required_skills": [
    {{"skill": "skill_name", "found": true, "evidence": "quote or null"}}
  ],
  "preferred_skills": [
    {{"skill": "skill_name", "found": false, "evidence": null}}
  ],
  "projects": [
    {{"title": "name", "technologies": ["tech"], "deployment_proof": false, "relevance": "low"}}
  ],
  "transferable_skills": [
    {{"skill": "name", "evidence": "quote"}}
  ],
  "experience_years": 0,
  "issues": [
    {{"type": "weak_evidence", "description": "note"}}
  ]
}}

JSON only:"""
        
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
            
            # Thread-safe model access with lock
            with self.model_lock:
                response = self.ai_runner.chat(
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.3,  # Low for consistency
                    stream=False
                )
            
            # Parse JSON response
            extracted_data = self._parse_json_response(response, cv_name)
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting data from CV {cv_name}: {e}")
            return self._get_empty_extraction()
    
    
    def _parse_json_response(self, response: str, cv_name: str = "unknown") -> Dict:
        """Parse AI JSON response with robust error handling and cleanup"""
        try:
            # Strategy 1: Try direct parsing first
            try:
                data = json.loads(response)
                return data
            except json.JSONDecodeError:
                pass
            
            # Strategy 2: Extract JSON block (handle markdown code fences)
            json_match = self.json_block_pattern.search(response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Strategy 3: Find first { to last }
                json_match = self.json_fallback_pattern.search(response)
                if not json_match:
                    logger.warning("No JSON found in AI response")
                    self._save_debug_response(response, cv_name, "no_json_found")
                    return self._get_empty_extraction()
                json_str = json_match.group(0)
            
            # Clean up common JSON issues
            json_str = self._clean_json_string(json_str)
            
            # Try to parse cleaned JSON
            data = json.loads(json_str)
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Response preview: {response[:300]}...")
            
            # Save failed response for debugging
            self._save_debug_response(response, cv_name, "json_error")
            
            # Last resort: try to salvage partial data
            try:
                return self._extract_partial_json(response)
            except:
                return self._get_empty_extraction()
        except Exception as e:
            logger.error(f"Unexpected error parsing JSON: {e}")
            return self._get_empty_extraction()
    
    def _save_debug_response(self, response: str, cv_name: str, error_type: str):
        """Save problematic AI responses for debugging"""
        try:
            debug_dir = Path("debug_responses")
            debug_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = debug_dir / f"{cv_name}_{error_type}_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"CV: {cv_name}\n")
                f.write(f"Error Type: {error_type}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write("="*80 + "\n")
                f.write(response)
            
            logger.info(f"Debug response saved to: {filename}")
        except Exception as e:
            logger.warning(f"Could not save debug response: {e}")
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean common JSON formatting issues using pre-compiled patterns"""
        # Remove trailing commas before } or ]
        json_str = self.trailing_comma_pattern.sub(r'\1', json_str)
        
        # Fix missing commas between array/object elements (common AI mistake)
        json_str = self.missing_comma_obj_pattern.sub(r'\1,\2', json_str)  # }{  -> },{
        json_str = self.missing_comma_arr_pattern.sub(r'\1,\2', json_str)  # ][  -> ],[
        
        # Remove control characters that break JSON
        json_str = ''.join(char for char in json_str if ord(char) >= 32 or char in '\n\r\t')
        
        return json_str
    
    def _extract_partial_json(self, response: str) -> Dict:
        """Attempt to extract partial data from malformed JSON"""
        logger.info("Attempting partial JSON extraction...")
        
        # Try to extract at least some skills using regex
        result = {
            "required_skills": [],
            "preferred_skills": [],
            "projects": [],
            "transferable_skills": [],
            "experience_years": 0,
            "issues": [{"type": "warning", "description": "Partial data extraction due to malformed JSON"}]
        }
        
        # Extract skill mentions using pre-compiled pattern
        for match in self.skill_pattern.finditer(response):
            skill_name = match.group(1)
            found = match.group(2).lower() == 'true'
            result["required_skills"].append({
                "skill": skill_name,
                "found": found,
                "evidence": None
            })
        
        return result
    
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
        # Quick exit if summaries disabled (avoid function overhead)
        if not self.enable_summaries:
            return self._quick_summary(extracted_data, score_result)
        
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
            
            # Thread-safe model access with lock
            with self.model_lock:
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
    
    def _quick_summary(self, extracted_data: Dict, score_result: Dict) -> str:
        """Generate fast summary without AI (when summaries disabled)"""
        req_found = sum(1 for s in extracted_data.get('required_skills', []) if s.get('found'))
        req_total = len(extracted_data.get('required_skills', []))
        return f"Score: {score_result['final_score']}/100 ({score_result['recommendation']}) - {req_found}/{req_total} required skills found"
    
    def _process_single_cv(self, cv_name: str, cv_text: str, job_description: str) -> Dict:
        """
        Process a single CV (thread-safe helper method)
        
        Args:
            cv_name: CV file name
            cv_text: Extracted CV text
            job_description: Job description text
            
        Returns:
            Analysis result dictionary
        """
        try:
            # Extract data with AI
            extracted_data = self.extract_cv_data(cv_text, job_description, cv_name)
            
            # Calculate score with Python (deterministic, fast)
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
            
            return result
        except Exception as e:
            logger.error(f"Error processing {cv_name}: {e}")
            # Return a minimal result even on error
            return {
                "cv_file": cv_name,
                "fit_score": 0,
                "recommendation": "ERROR",
                "summary": f"Processing failed: {str(e)}",
                "breakdown": ["Error during processing"],
                "extracted_data": {},
                "details": {},
                "cv_text_preview": cv_text[:500] if cv_text else ""
            }
    
    def process_all_cvs(self, cv_directory: str, job_description: str, batch_size: int = 4, progress_callback=None) -> List[Dict]:
        """
        Process all CVs in the directory and analyze them (with parallel AI extraction)
        
        Args:
            cv_directory: Path to directory containing CVs
            job_description: Job description text
            batch_size: Number of CVs to process in each batch (deprecated, use config.parallel_workers)
            progress_callback: Optional callback function(current, total, elapsed_time)
            
        Returns:
            List of analysis results for each CV
        """
        import time
        start_time = time.time()
        
        # Step 1: Get all CV files
        cv_files = self.get_cv_files(cv_directory)
        
        # Step 2: Extract text in parallel
        print(f"\n{'='*60}")
        print(f"Extracting text from {len(cv_files)} CVs...")
        print(f"{'='*60}\n")
        
        if progress_callback:
            progress_callback(0, len(cv_files), 0)
            
        cv_texts = self.extract_cvs_parallel(cv_files, max_workers=self.pdf_workers)
        
        if not cv_texts:
            logger.error("No CVs with sufficient text found!")
            return []
        
        # Step 3: Process CVs with parallel AI extraction
        cv_items = list(cv_texts.items())
        total_cvs = len(cv_items)
        
        logger.info(f"Processing {total_cvs} CVs with {self.parallel_workers} parallel workers...")
        logger.info(f"Summary generation: {'ENABLED' if self.enable_summaries else 'DISABLED (for speed)'}")
        print(f"\n{'='*60}")
        print(f"Analyzing {total_cvs} CVs against job description")
        print(f"Workers: {self.parallel_workers} | Summaries: {'ON' if self.enable_summaries else 'OFF'}")
        print(f"{'='*60}\n")
        
        results = []
        completed = 0
        
        # Use ThreadPoolExecutor for parallel AI extraction
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submit all CV processing tasks
            future_to_cv = {
                executor.submit(self._process_single_cv, cv_name, cv_text, job_description): cv_name
                for cv_name, cv_text in cv_items
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_cv):
                cv_name = future_to_cv[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    # Calculate elapsed time
                    elapsed = time.time() - start_time
                    
                    # Progress reporting
                    print(f"[{completed}/{total_cvs}] ✓ {cv_name}: {result['fit_score']}/100 | {result['recommendation']}")
                    
                    if progress_callback:
                        progress_callback(completed, total_cvs, elapsed)
                    
                except Exception as e:
                    logger.error(f"Failed to get result for {cv_name}: {e}")
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total_cvs, time.time() - start_time)
        
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
