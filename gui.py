"""
Modular CV Scanner GUI - Premium Edition
A modern, component-based GUI for CV analysis using CustomTkinter

Architecture:
- Separated UI components into modular classes
- Centralized theme management
- Clear separation of concerns
- Event-driven architecture
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import os
from main import CVAnalyzer

from components import (
    ThemeManager,
    Sidebar,
    MainPanel,
    DetailsModal,
    ExportDialog
)


class CVScannerModular(ctk.CTk):
    """Main application class - coordinates all components"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("CV Analysis Tool - Modular Edition")
        self.geometry("1200x850")
        
        # Grid configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Apply theme
        ThemeManager.apply_theme("dark")
        
        # Application state
        self.analyzer = None
        self.analyzer_lock = threading.Lock()
        self.all_candidates = []
        self.filtered_candidates = []
        self.analysis_stats = {"total": 0, "shortlist": 0, "review": 0, "reject": 0}
        
        # Create components
        self._create_components()
        
        # Initialize analyzer in background
        self.after(100, self._initialize_analyzer)
    
    def _create_components(self):
        """Create and configure all UI components"""
        # Sidebar
        self.sidebar = Sidebar(
            self,
            on_browse_callback=self._on_directory_selected,
            on_run_callback=self._on_run_analysis,
            on_appearance_change=self._on_appearance_changed
        )
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        
        # Main panel
        self.main_panel = MainPanel(
            self,
            on_search_callback=self._on_search,
            on_sort_callback=self._on_sort,
            on_filter_callback=self._on_filter,
            on_export_callback=self._on_export,
            on_details_callback=self._on_view_details
        )
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)
    
    def _initialize_analyzer(self):
        """Initialize the AI analyzer (runs once at startup)"""
        try:
            self.sidebar.set_status("🔄 Loading AI model...", ThemeManager.COLORS["warning"])
            self.analyzer = CVAnalyzer()
            self.sidebar.set_status("✓ Ready to analyze", ThemeManager.COLORS["success"])
            self._show_toast("AI model loaded and ready!", "success")
        except Exception as e:
            self.sidebar.set_status(f"❌ Model load failed: {str(e)}", ThemeManager.COLORS["danger"])
            messagebox.showerror("Initialization Error", f"Failed to load AI model:\n\n{str(e)}")
    
    # Event handlers
    def _on_directory_selected(self, directory):
        """Handle directory selection"""
        self.sidebar.set_status(f"✓ Selected: {os.path.basename(directory)}", ThemeManager.COLORS["success"])
        
        # Count files
        try:
            files = [f for f in os.listdir(directory) if f.endswith(('.pdf', '.docx', '.doc'))]
            self._show_toast(f"Found {len(files)} CV files", "info")
        except:
            pass
    
    def _on_run_analysis(self, cv_dir):
        """Handle run analysis button click"""
        job_description = self.main_panel.get_job_description()
        
        if not cv_dir or not job_description:
            messagebox.showerror("Missing Input", "Please provide both a CV directory and a job description.")
            return
        
        if not os.path.isdir(cv_dir):
            messagebox.showerror("Invalid Directory", "The specified CV directory does not exist.")
            return
        
        # UI updates
        self.sidebar.set_run_button_state(analyzing=True)
        self.sidebar.show_progress(True)
        self.sidebar.set_status("🔄 Analysis in progress...", ThemeManager.COLORS["warning"])
        
        # Clear previous results
        self.main_panel.clear_results()
        self.all_candidates.clear()
        self.filtered_candidates.clear()
        self.sidebar.hide_stats()
        
        # Start analysis thread
        thread = threading.Thread(
            target=self._run_analysis,
            args=(cv_dir, job_description),
            daemon=True
        )
        thread.start()
    
    def _run_analysis(self, cv_dir, job_description):
        """Run CV analysis (in background thread)"""
        try:
            # Check analyzer
            if self.analyzer is None:
                raise RuntimeError("AI model not loaded. Please wait for initialization.")
            
            # Update analyzer config
            settings = self.sidebar.get_settings()
            with self.analyzer_lock:
                self.analyzer.parallel_workers = settings["parallel_workers"]
                self.analyzer.enable_summaries = settings["enable_summaries"]
            
            # Define progress callback
            def progress_callback(current, total, elapsed):
                self.after(0, self.sidebar.update_progress, current, total, elapsed)
            
            # Process CVs
            all_results = self.analyzer.process_all_cvs(
                cv_dir, 
                job_description, 
                progress_callback=progress_callback
            )
            
            # Store and categorize
            self.all_candidates = all_results
            
            # Calculate stats
            self.analysis_stats = {
                "total": len(all_results),
                "shortlist": sum(1 for r in all_results if "SHORTLIST" in r.get("recommendation", "").upper()),
                "review": sum(1 for r in all_results if "REVIEW" in r.get("recommendation", "").upper()),
                "reject": sum(1 for r in all_results if "SHORTLIST" not in r.get("recommendation", "").upper() and "REVIEW" not in r.get("recommendation", "").upper())
            }
            
            top_candidates = self.analyzer.get_top_candidates(all_results, top_n=20)
            
            # Update UI on main thread
            self.after(0, self._on_analysis_complete, top_candidates)
        except Exception as e:
            self.after(0, self._on_analysis_error, str(e))
    
    def _on_analysis_complete(self, candidates):
        """Handle analysis completion"""
        self.sidebar.show_progress(False)
        self.sidebar.set_run_button_state(analyzing=False)
        self.sidebar.set_status("✅ Analysis complete!", ThemeManager.COLORS["success"])
        
        # Display results
        self.main_panel.display_results(candidates)
        self.filtered_candidates = candidates
        
        # Show stats
        self.sidebar.show_stats(self.analysis_stats)
        
        messagebox.showinfo(
            "Analysis Complete",
            f"Successfully analyzed {self.analysis_stats['total']} candidates!\n\n"
            f"Shortlisted: {self.analysis_stats['shortlist']}\n"
            f"For Review: {self.analysis_stats['review']}"
        )
    
    def _on_analysis_error(self, error_message):
        """Handle analysis error"""
        self.sidebar.show_progress(False)
        self.sidebar.set_run_button_state(analyzing=False)
        self.sidebar.set_status("❌ Analysis failed", ThemeManager.COLORS["danger"])
        messagebox.showerror("Analysis Failed", f"An error occurred during analysis:\n\n{error_message}")
    
    def _on_search(self):
        """Handle search query"""
        self._apply_filters()
    
    def _on_sort(self, choice):
        """Handle sort selection"""
        if "Score" in choice:
            self.all_candidates.sort(key=lambda x: float(x.get("fit_score", 0)), reverse=True)
        elif "Name ↑" in choice:
            self.all_candidates.sort(key=lambda x: os.path.basename(x.get("cv_file", "")))
        elif "Name ↓" in choice:
            self.all_candidates.sort(key=lambda x: os.path.basename(x.get("cv_file", "")), reverse=True)
        
        self._apply_filters()
    
    def _on_filter(self, choice):
        """Handle filter selection"""
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply search and filter to candidates"""
        search_query = self.main_panel.get_search_query()
        filter_value = self.main_panel.filter_menu.get()
        
        if not search_query and filter_value == "All":
            self.main_panel.display_results(self.all_candidates[:20])
            return
        
        filtered = []
        for candidate in self.all_candidates:
            name = os.path.basename(candidate.get("cv_file", "")).lower()
            rec = candidate.get("recommendation", "").upper()
            
            # Apply search filter
            if search_query and search_query not in name:
                continue
            
            # Apply recommendation filter
            if filter_value != "All":
                if filter_value == "Shortlist" and "SHORTLIST" not in rec:
                    continue
                elif filter_value == "Review" and "REVIEW" not in rec:
                    continue
                elif filter_value == "Other" and ("SHORTLIST" in rec or "REVIEW" in rec):
                    continue
            
            filtered.append(candidate)
        
        self.main_panel.display_results(filtered[:20])
    
    def _on_export(self):
        """Handle export button click"""
        if not self.all_candidates:
            messagebox.showinfo("No Data", "Please run an analysis first to generate results for export.")
            return
        
        ExportDialog(self, self.all_candidates, self.analysis_stats)
    
    def _on_view_details(self, candidate_data):
        """Handle view details button click"""
        DetailsModal(self, candidate_data)
    
    def _on_appearance_changed(self, new_mode):
        """Handle theme/appearance change"""
        ctk.set_appearance_mode(new_mode)
        self._show_toast(f"Theme changed to {new_mode}", "info")
    
    def _show_toast(self, message, toast_type="info"):
        """Show toast notification"""
        colors = {
            "success": ThemeManager.COLORS["success"],
            "error": ThemeManager.COLORS["danger"],
            "warning": ThemeManager.COLORS["warning"],
            "info": ThemeManager.COLORS["info"]
        }
        self.sidebar.set_status(f"ℹ️ {message}", colors.get(toast_type, ThemeManager.COLORS["info"]))


def main():
    """Application entry point"""
    app = CVScannerModular()
    app.mainloop()


if __name__ == "__main__":
    main()
