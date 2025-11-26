import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import json
import csv
from datetime import datetime
from main import CVAnalyzer

# Appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Load styles
STYLES = {
    "colors": {
        "primary_gradient": ["#667eea", "#764ba2"],
        "success_gradient": ["#56ab2f", "#a8e063"],
        "warning_gradient": ["#f2994a", "#f2c94c"],
        "info_gradient": ["#4facfe", "#00f2fe"],
        "primary": "#667eea",
        "success": "#56ab2f",
        "warning": "#f2994a",
        "danger": "#eb3349",
        "info": "#4facfe",
    }
}


class CVScannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CV Analysis Tool - Premium Edition")
        self.geometry("1200x850")
        
        # Grid configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Data
        self.analysis_data = {}
        self.results_widgets = []
        self.all_candidates = []
        self.filtered_candidates = []
        self.current_sort = "score"
        self.current_filter = "All"
        self.analysis_stats = {"total": 0, "shortlist": 0, "review": 0, "reject": 0}

        # Build UI
        self.create_sidebar()
        self.create_main_panel()
        
        # Add animation state
        self.animation_running = False

    # -----------------------
    # Sidebar
    # -----------------------
    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=("#f8f9fa", "#16213e"))
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)
        self.sidebar_frame.grid_propagate(False)

        # Logo with modern styling
        self.logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=(30, 5), sticky="ew")
        
        self.logo_label = ctk.CTkLabel(
            self.logo_frame, 
            text="CV Scanner", 
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=("#5568d3", "#667eea")
        )
        self.logo_label.pack()

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="✨ AI-Powered Analysis",
            font=ctk.CTkFont(size=13),
            text_color=("#6b7280", "#a0aec0"),
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 30))

        # Divider
        divider1 = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color=("#e5e7eb", "#2d3748"))
        divider1.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        # CV Directory Section
        self.dir_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="📂 CV Directory", 
            font=ctk.CTkFont(size=15, weight="bold"), 
            anchor="w"
        )
        self.dir_label.grid(row=3, column=0, padx=20, pady=(0, 8), sticky="w")

        self.dir_entry = ctk.CTkEntry(
            self.sidebar_frame, 
            placeholder_text="Select folder with CVs...", 
            height=42,
            corner_radius=10,
            border_width=2,
            border_color=("#d1d5db", "#2d3748")
        )
        self.dir_entry.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.browse_button = ctk.CTkButton(
            self.sidebar_frame,
            text="📁 Browse Folder",
            command=self.browse_directory,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=("#667eea", "#667eea"),
            hover_color=("#5568d3", "#5568d3"),
        )
        self.browse_button.grid(row=5, column=0, padx=20, pady=(0, 25), sticky="ew")

        # Run Analysis Button
        self.run_button = ctk.CTkButton(
            self.sidebar_frame,
            text="🚀 Start Analysis",
            command=self.run_analysis_thread,
            height=55,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=12,
            fg_color="transparent",
            border_width=2,
            border_color=("#667eea", "#667eea"),
            text_color=("#5568d3", "#ffffff"),
            hover_color=("#e0e7ff", "#667eea"),
        )
        self.run_button.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Progress Section
        self.progress_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.progress_frame.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="new")
        self.progress_frame.grid_remove()

        self.progress_label = ctk.CTkLabel(
            self.progress_frame, 
            text="Processing...", 
            font=ctk.CTkFont(size=12),
            text_color=("#6b7280", "#a0aec0")
        )
        self.progress_label.pack(pady=(0, 5))

        self.progress = ctk.CTkProgressBar(self.progress_frame, mode="indeterminate", height=8)
        self.progress.pack(fill="x")

        self.progress_percent = ctk.CTkLabel(
            self.progress_frame, 
            text="0%", 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#667eea", "#667eea")
        )
        self.progress_percent.pack(pady=(5, 0))

        # Stats Section
        self.stats_frame = ctk.CTkFrame(self.sidebar_frame, corner_radius=10, fg_color=("#ffffff", "#0f1419"))
        self.stats_frame.grid(row=8, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.stats_frame.grid_remove()

        stats_title = ctk.CTkLabel(
            self.stats_frame, 
            text="📊 Analysis Stats", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        stats_title.pack(pady=(10, 5))

        self.stats_text = ctk.CTkLabel(
            self.stats_frame, 
            text="", 
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        self.stats_text.pack(pady=(0, 10), padx=10)

        # Appearance selector
        self.appearance_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="🎨 Theme", 
            anchor="w", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.appearance_label.grid(row=9, column=0, padx=20, pady=(10, 8), sticky="w")

        self.appearance_mode = ctk.CTkOptionMenu(
            self.sidebar_frame, 
            values=["Dark", "Light", "System"], 
            command=self.change_appearance_mode, 
            height=38,
            corner_radius=10,
            fg_color=("#667eea", "#667eea"),
            button_color=("#5568d3", "#5568d3"),
            button_hover_color=("#4451b8", "#4451b8")
        )
        self.appearance_mode.grid(row=10, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.appearance_mode.set("Dark")

        # Status with modern styling
        self.status_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="✓ Ready to analyze", 
            font=ctk.CTkFont(size=12), 
            text_color=("#56ab2f", "#56ab2f"), 
            anchor="w"
        )
        self.status_label.grid(row=11, column=0, padx=20, pady=(0, 25), sticky="sw")

    # -----------------------
    # Main panel
    # -----------------------
    def create_main_panel(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=2)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Job description section
        jd_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        jd_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        jd_header.grid_columnconfigure(0, weight=1)

        self.jd_label = ctk.CTkLabel(
            jd_header, 
            text="📝 Job Description", 
            font=ctk.CTkFont(size=20, weight="bold"), 
            anchor="w"
        )
        self.jd_label.grid(row=0, column=0, sticky="w")

        self.char_count_label = ctk.CTkLabel(
            jd_header, 
            text="0 characters", 
            font=ctk.CTkFont(size=11), 
            text_color=("#6b7280", "#718096"),
            anchor="e"
        )
        self.char_count_label.grid(row=0, column=1, sticky="e")

        # Job description textbox with modern styling
        self.jd_textbox = ctk.CTkTextbox(
            self.main_frame, 
            font=ctk.CTkFont(size=13), 
            wrap="word", 
            height=200,
            corner_radius=12,
            border_width=2,
            border_color=("#d1d5db", "#2d3748")
        )
        self.jd_textbox.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        self.jd_textbox.bind("<KeyRelease>", self.update_char_count)

        # Results header with controls
        results_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        results_header.grid(row=2, column=0, sticky="ew", pady=(10, 10))
        results_header.grid_columnconfigure(1, weight=1)

        self.results_label = ctk.CTkLabel(
            results_header, 
            text="🏆 Top Candidates", 
            font=ctk.CTkFont(size=20, weight="bold"), 
            anchor="w"
        )
        self.results_label.grid(row=0, column=0, sticky="w", padx=(0, 15))

        # Search box
        self.search_entry = ctk.CTkEntry(
            results_header, 
            placeholder_text="🔍 Search candidates...", 
            height=36,
            width=200,
            corner_radius=8
        )
        self.search_entry.grid(row=0, column=1, sticky="e", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_results())

        # Sort dropdown
        self.sort_menu = ctk.CTkOptionMenu(
            results_header,
            values=["Sort: Score ↓", "Sort: Name ↑", "Sort: Name ↓"],
            command=self.sort_results,
            height=36,
            width=140,
            corner_radius=8,
            fg_color=("#4c51bf", "#667eea"),
            button_color=("#434190", "#5568d3"),
            button_hover_color=("#3c366b", "#4451b8")
        )
        self.sort_menu.grid(row=0, column=2, sticky="e", padx=(0, 10))
        self.sort_menu.set("Sort: Score ↓")

        # Filter dropdown
        self.filter_menu = ctk.CTkOptionMenu(
            results_header,
            values=["All", "Shortlist", "Review", "Other"],
            command=self.filter_by_recommendation,
            height=36,
            width=120,
            corner_radius=8,
            fg_color=("#3182ce", "#4facfe"),
            button_color=("#2b6cb0", "#3d8dce"),
            button_hover_color=("#2c5282", "#2c6ea0")
        )
        self.filter_menu.grid(row=0, column=3, sticky="e", padx=(0, 10))
        self.filter_menu.set("All")

        # Export button
        self.export_btn = ctk.CTkButton(
            results_header,
            text="💾 Export",
            command=self.show_export_menu,
            height=36,
            width=100,
            corner_radius=8,
            fg_color=("#38a169", "#56ab2f"),
            hover_color=("#2f855a", "#469024"),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffffff"
        )
        self.export_btn.grid(row=0, column=4, sticky="e")

        # Results scrollable frame with modern styling
        self.results_frame = ctk.CTkScrollableFrame(
            self.main_frame, 
            label_text="", 
            corner_radius=12,
            fg_color=("#f3f4f6", "#1a202c"),
            border_width=2,
            border_color=("#e5e7eb", "#2d3748")
        )
        self.results_frame.grid(row=3, column=0, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)

    # -----------------------
    # Event handlers
    # -----------------------
    def update_char_count(self, event=None):
        """Update character count for job description"""
        content = self.jd_textbox.get("1.0", "end-1c")
        char_count = len(content)
        self.char_count_label.configure(text=f"{char_count} characters")

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, directory)
            self.update_status(f"✓ Selected: {os.path.basename(directory)}", "#56ab2f")
            
            # Count files
            files = [f for f in os.listdir(directory) if f.endswith(('.pdf', '.docx', '.doc'))]
            self.show_toast(f"Found {len(files)} CV files", "info")

    def show_toast(self, message, type="info"):
        """Show a toast notification"""
        colors = {
            "success": "#56ab2f",
            "error": "#eb3349",
            "warning": "#f2994a",
            "info": "#4facfe"
        }
        self.update_status(f"ℹ️ {message}", colors.get(type, "#4facfe"))

    # -----------------------
    # Analysis
    # -----------------------
    def run_analysis_thread(self):
        cv_dir = self.dir_entry.get().strip()
        job_description = self.jd_textbox.get("1.0", "end").strip()

        if not cv_dir or not job_description:
            messagebox.showerror("Missing Input", "Please provide both a CV directory and a job description.")
            return
        if not os.path.isdir(cv_dir):
            messagebox.showerror("Invalid Directory", "The specified CV directory does not exist.")
            return

        # UI changes
        self.run_button.configure(
            state="disabled", 
            text="⏳ Analyzing...",
            fg_color=("#667eea", "#667eea"),
            text_color="#ffffff"
        )
        self.progress_frame.grid()
        self.progress.start()
        self.update_status("🔄 Analysis in progress...", "#f2994a")

        # Clear previous results
        for widget in self.results_widgets:
            try:
                widget.destroy()
            except Exception:
                pass
        self.results_widgets.clear()
        self.analysis_data.clear()
        self.all_candidates.clear()
        self.filtered_candidates.clear()
        self.stats_frame.grid_remove()

        # Start thread
        thread = threading.Thread(target=self.run_analysis, args=(cv_dir, job_description), daemon=True)
        thread.start()

    def run_analysis(self, cv_dir, job_description):
        try:
            analyzer = CVAnalyzer()
            all_results = analyzer.process_all_cvs(cv_dir, job_description)
            
            # Store and categorize
            self.analysis_data = {os.path.basename(res["cv_file"]): res for res in all_results}
            self.all_candidates = all_results
            
            # Calculate stats
            self.analysis_stats = {
                "total": len(all_results),
                "shortlist": sum(1 for r in all_results if "SHORTLIST" in r.get("recommendation", "").upper()),
                "review": sum(1 for r in all_results if "REVIEW" in r.get("recommendation", "").upper()),
                "reject": sum(1 for r in all_results if "SHORTLIST" not in r.get("recommendation", "").upper() and "REVIEW" not in r.get("recommendation", "").upper())
            }
            
            top_candidates = analyzer.get_top_candidates(all_results, top_n=20)
            
            # Update UI on main thread
            self.after(0, self.update_results, top_candidates)
        except Exception as e:
            self.after(0, lambda: self.show_error(f"An error occurred during analysis:\n\n{str(e)}"))
        finally:
            self.after(0, self.analysis_complete)

    # -----------------------
    # Results UI
    # -----------------------
    def update_results(self, candidates):
        """Update results display with candidate cards"""
        for widget in self.results_widgets:
            try:
                widget.destroy()
            except Exception:
                pass
        self.results_widgets.clear()

        if not candidates:
            no_results = ctk.CTkLabel(
                self.results_frame, 
                text="No candidates found matching the criteria", 
                font=ctk.CTkFont(size=15),
                text_color=("#6b7280", "#718096")
            )
            no_results.grid(row=0, column=0, pady=50)
            self.results_widgets.append(no_results)
            return

        # Animate cards appearing
        for i, candidate in enumerate(candidates):
            card = self.create_candidate_card(self.results_frame, i, candidate)
            card.grid(row=i, column=0, padx=0, pady=6, sticky="ew")
            self.results_widgets.append(card)
            
            # Stagger animation
            self.after(i * 30, lambda c=card: self.animate_card_in(c))

        self.filtered_candidates = candidates

    def animate_card_in(self, card):
        """Simple fade-in animation for cards"""
        try:
            card.configure(border_width=2)
        except:
            pass

    def create_candidate_card(self, parent, rank, candidate):
        """Create a modern candidate card with gradients and hover effects"""
        rec = candidate.get("recommendation", "").upper()
        
        # Modern color scheme
        if "SHORTLIST" in rec:
            border_color = "#56ab2f"
            rec_color = "#56ab2f"
            rank_bg = "#56ab2f"
        elif "REVIEW" in rec:
            border_color = "#4facfe"
            rec_color = "#4facfe"
            rank_bg = "#4facfe"
        else:
            border_color = "#a0aec0"
            rec_color = "#a0aec0"
            rank_bg = "#718096"

        card_frame = ctk.CTkFrame(
            parent, 
            corner_radius=12, 
            border_width=2, 
            border_color=border_color,
            fg_color=("#ffffff", "#1e2433")
        )
        card_frame.grid_columnconfigure(1, weight=1)

        # Rank badge with modern styling
        rank_label = ctk.CTkLabel(
            card_frame, 
            text=f"#{rank + 1}", 
            font=ctk.CTkFont(size=22, weight="bold"), 
            width=60,
            height=60,
            fg_color=rank_bg, 
            corner_radius=10,
            text_color="#ffffff"
        )
        rank_label.grid(row=0, column=0, rowspan=2, padx=15, pady=15, sticky="n")

        # Info section
        info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, columnspan=2, padx=(0, 15), pady=(15, 5), sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)

        # Name with better styling
        name_text = os.path.basename(candidate.get("cv_file", "Unknown"))
        if len(name_text) > 50:
            name_text = name_text[:47] + "..."
        
        name_label = ctk.CTkLabel(
            info_frame, 
            text=name_text, 
            font=ctk.CTkFont(size=16, weight="bold"), 
            anchor="w"
        )
        name_label.grid(row=0, column=0, sticky="w")

        # Score and badge section
        score_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        score_frame.grid(row=1, column=1, padx=(0, 10), pady=(0, 15), sticky="w")

        # Animated score bar
        fit_score_value = candidate.get("fit_score", 0)
        try:
            score_num = float(fit_score_value)
            score_text = f"Match: {score_num:.0f}%"
        except Exception:
            score_num = 0
            score_text = f"Match: {fit_score_value}"

        score_container = ctk.CTkFrame(score_frame, fg_color="transparent")
        score_container.grid(row=0, column=0, sticky="w")

        score_label = ctk.CTkLabel(
            score_container, 
            text=score_text, 
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        score_label.pack(anchor="w", pady=(0, 3))

        # Score bar
        score_bar_bg = ctk.CTkFrame(score_container, height=6, width=150, corner_radius=3, fg_color=("#e2e8f0", "#2d3748"))
        score_bar_bg.pack(anchor="w")
        
        try:
            bar_width = int((score_num / 100) * 150)
            score_bar = ctk.CTkFrame(score_bar_bg, height=6, width=bar_width, corner_radius=3, fg_color=border_color)
            score_bar.place(x=0, y=0)
        except:
            pass

        # Recommendation badge
        rec_badge = ctk.CTkLabel(
            score_frame,
            text=candidate.get("recommendation", "N/A"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff",
            fg_color=rec_color,
            corner_radius=8,
            padx=12,
            pady=6,
        )
        rec_badge.grid(row=0, column=1, padx=(15, 0))

        # Skills tags (if available)
        extracted = candidate.get("extracted_data", {})
        if extracted.get("required_skills"):
            found_skills = [s for s in extracted["required_skills"] if s.get("found")][:3]
            if found_skills:
                skills_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                skills_frame.grid(row=2, column=1, padx=(0, 10), pady=(0, 12), sticky="w")
                
                for idx, skill in enumerate(found_skills):
                    skill_tag = ctk.CTkLabel(
                        skills_frame,
                        text=f"✓ {skill['skill'][:15]}",
                        font=ctk.CTkFont(size=10),
                        fg_color=("#e6ffed", "#1a3d2e"),
                        text_color=("#22863a", "#56ab2f"),
                        corner_radius=5,
                        padx=8,
                        pady=3
                    )
                    skill_tag.grid(row=0, column=idx, padx=(0, 5))

        # View details button with modern styling
        details_btn = ctk.CTkButton(
            card_frame,
            text="View Details →",
            command=lambda c=candidate: self.show_cv_details_modern(c),
            width=130,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            fg_color="transparent",
            border_width=2,
            border_color=border_color,
            text_color=border_color,
            hover_color=border_color,
        )
        details_btn.grid(row=1, column=2, rowspan=2, padx=(0, 15), pady=(0, 15), sticky="e")

        return card_frame

    # -----------------------
    # Filter and Sort
    # -----------------------
    def filter_results(self):
        """Filter results based on search query"""
        search_query = self.search_entry.get().lower()
        
        if not search_query and self.current_filter == "All":
            self.update_results(self.all_candidates[:20])
            return
        
        filtered = []
        for candidate in self.all_candidates:
            name = os.path.basename(candidate.get("cv_file", "")).lower()
            rec = candidate.get("recommendation", "").upper()
            
            # Apply search filter
            if search_query and search_query not in name:
                continue
            
            # Apply recommendation filter
            if self.current_filter != "All":
                if self.current_filter == "Shortlist" and "SHORTLIST" not in rec:
                    continue
                elif self.current_filter == "Review" and "REVIEW" not in rec:
                    continue
                elif self.current_filter == "Other" and ("SHORTLIST" in rec or "REVIEW" in rec):
                    continue
            
            filtered.append(candidate)
        
        self.update_results(filtered[:20])

    def sort_results(self, choice):
        """Sort results based on selection"""
        if "Score" in choice:
            self.all_candidates.sort(key=lambda x: float(x.get("fit_score", 0)), reverse=True)
        elif "Name ↑" in choice:
            self.all_candidates.sort(key=lambda x: os.path.basename(x.get("cv_file", "")))
        elif "Name ↓" in choice:
            self.all_candidates.sort(key=lambda x: os.path.basename(x.get("cv_file", "")), reverse=True)
        
        self.filter_results()

    def filter_by_recommendation(self, choice):
        """Filter by recommendation type"""
        self.current_filter = choice
        self.filter_results()

    # -----------------------
    # Export functionality
    # -----------------------
    def show_export_menu(self):
        """Show export options"""
        if not self.all_candidates:
            messagebox.showinfo("No Data", "Please run an analysis first to generate results for export.")
            return

        export_window = ctk.CTkToplevel(self)
        export_window.title("Export Results")
        export_window.geometry("400x250")
        export_window.transient(self)
        
        # Center the window
        export_window.grab_set()
        
        title = ctk.CTkLabel(
            export_window, 
            text="📊 Export Analysis Results", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(20, 10))
        
        subtitle = ctk.CTkLabel(
            export_window, 
            text="Choose your export format", 
            font=ctk.CTkFont(size=12),
            text_color=("#a0aec0", "#718096")
        )
        subtitle.pack(pady=(0, 20))
        
        # Export buttons
        csv_btn = ctk.CTkButton(
            export_window,
            text="📄 Export as CSV",
            command=lambda: [self.export_csv(), export_window.destroy()],
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=("#56ab2f", "#56ab2f"),
            hover_color=("#469024", "#469024")
        )
        csv_btn.pack(pady=5, padx=30, fill="x")
        
        json_btn = ctk.CTkButton(
            export_window,
            text="📋 Export as JSON",
            command=lambda: [self.export_json(), export_window.destroy()],
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=("#4facfe", "#4facfe"),
            hover_color=("#3d8dce", "#3d8dce")
        )
        json_btn.pack(pady=5, padx=30, fill="x")
        
        cancel_btn = ctk.CTkButton(
            export_window,
            text="Cancel",
            command=export_window.destroy,
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=10,
            fg_color="transparent",
            border_width=2,
            border_color=("#a0aec0", "#718096"),
            text_color=("#a0aec0", "#718096")
        )
        cancel_btn.pack(pady=(5, 20), padx=30, fill="x")

    def export_csv(self):
        """Export results to CSV"""
        if not self.all_candidates:
            messagebox.showwarning("No Data", "No analysis data available to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"cv_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Rank", "CV File", "Fit Score", "Recommendation"])
                
                for i, candidate in enumerate(self.all_candidates, 1):
                    writer.writerow([
                        i,
                        os.path.basename(candidate.get("cv_file", "")),
                        candidate.get("fit_score", ""),
                        candidate.get("recommendation", "")
                    ])
            
            messagebox.showinfo("Success", f"Results exported successfully to:\n{filename}")
            self.show_toast("CSV exported successfully", "success")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export CSV:\n{str(e)}")

    def export_json(self):
        """Export results to JSON"""
        if not self.all_candidates:
            messagebox.showwarning("No Data", "No analysis data available to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"cv_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if not filename:
            return
        
        try:
            export_data = {
                "analysis_date": datetime.now().isoformat(),
                "total_candidates": len(self.all_candidates),
                "statistics": self.analysis_stats,
                "candidates": self.all_candidates
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Results exported successfully to:\n{filename}")
            self.show_toast("JSON exported successfully", "success")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export JSON:\n{str(e)}")

    # -----------------------
    # Analysis complete / errors
    # -----------------------
    def analysis_complete(self):
        """Called when analysis is complete"""
        try:
            self.progress.stop()
            self.progress_frame.grid_remove()
            self.run_button.configure(
                state="normal", 
                text="🚀 Start Analysis",
                fg_color="transparent",
                text_color=("#667eea", "#667eea")
            )
            self.update_status("✅ Analysis complete!", "#56ab2f")
            
            # Show stats
            self.stats_frame.grid()
            stats_text = (
                f"Total: {self.analysis_stats['total']}\n"
                f"✓ Shortlist: {self.analysis_stats['shortlist']}\n"
                f"● Review: {self.analysis_stats['review']}\n"
                f"✗ Other: {self.analysis_stats['reject']}"
            )
            self.stats_text.configure(text=stats_text)
            
            messagebox.showinfo("Analysis Complete", 
                f"Successfully analyzed {self.analysis_stats['total']} candidates!\n\n"
                f"Shortlisted: {self.analysis_stats['shortlist']}\n"
                f"For Review: {self.analysis_stats['review']}")
        except Exception:
            pass

    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Analysis Failed", message)
        self.update_status("❌ Analysis failed", "#eb3349")

    def update_status(self, message, color=None):
        """Update status label with optional color"""
        try:
            self.status_label.configure(text=message)
            if color:
                self.status_label.configure(text_color=color)
        except Exception:
            pass

    # -----------------------
    # Details popup (enhanced)
    # -----------------------
    def show_cv_details_modern(self, data):
        """Show detailed CV analysis in a modern modal"""
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"Analysis Details - {os.path.basename(data.get('cv_file',''))}")
        details_window.geometry("900x950")
        details_window.grid_columnconfigure(0, weight=1)
        details_window.grid_rowconfigure(1, weight=1)

        # Window behavior
        try:
            details_window.transient(self)
            details_window.lift()
            details_window.attributes("-topmost", True)
            details_window.focus_force()
            details_window.after(200, lambda: details_window.attributes("-topmost", False))
        except Exception:
            pass

        # Modern header with gradient effect
        header_frame = ctk.CTkFrame(details_window, corner_radius=0, height=100, fg_color=("#667eea", "#5568d3"))
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_propagate(False)

        title_label = ctk.CTkLabel(
            header_frame, 
            text=os.path.basename(data.get("cv_file", "Unknown")), 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#ffffff"
        )
        title_label.grid(row=0, column=0, padx=30, pady=(25, 5), sticky="w")

        score_text = f"🎯 Match Score: {data.get('fit_score', 'N/A')}%  •  {data.get('recommendation', '')}"
        score_label = ctk.CTkLabel(
            header_frame, 
            text=score_text, 
            font=ctk.CTkFont(size=14),
            text_color="#ffffff"
        )
        score_label.grid(row=1, column=0, padx=30, pady=(0, 25), sticky="w")

        # Copy button
        copy_btn = ctk.CTkButton(
            header_frame,
            text="📋 Copy",
            command=lambda: self.copy_to_clipboard(data),
            width=90,
            height=35,
            corner_radius=8,
            fg_color="#ffffff",
            text_color=("#667eea", "#667eea"),
            hover_color=("#f0f0f0", "#f0f0f0"),
            font=ctk.CTkFont(size=12, weight="bold")
        )
        copy_btn.grid(row=0, column=1, rowspan=2, padx=30, pady=25, sticky="e")

        # Scrollable content
        content_frame = ctk.CTkScrollableFrame(details_window, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=25)
        content_frame.grid_columnconfigure(0, weight=1)

        row_idx = 0

        # Summary section
        if data.get("summary"):
            self.add_section(content_frame, row_idx, "📋 Overall Summary", data["summary"])
            row_idx += 1

        # Score breakdown
        if data.get("breakdown"):
            breakdown_text = "\n".join(data["breakdown"])
            self.add_section(content_frame, row_idx, "📊 Score Breakdown", breakdown_text, "#667eea")
            row_idx += 1

        # Skills analysis
        extracted = data.get("extracted_data", {})
        if extracted.get("required_skills"):
            found_skills = [s for s in extracted["required_skills"] if s.get("found")]
            missing_skills = [s for s in extracted["required_skills"] if not s.get("found")]
            
            if found_skills:
                skills_text = "\n".join([
                    f"✓ {s['skill']}: {s.get('evidence', 'N/A')[:100]}..." 
                    for s in found_skills
                ])
                self.add_section(content_frame, row_idx, "✨ Required Skills Found", skills_text, "#56ab2f")
                row_idx += 1
            
            if missing_skills:
                missing_text = "\n".join([f"✗ {s['skill']}" for s in missing_skills])
                self.add_section(content_frame, row_idx, "⚠️ Missing Required Skills", missing_text, "#eb3349")
                row_idx += 1

        # Projects
        if extracted.get("projects"):
            projects_text = "\n\n".join([
                f"• {p.get('title', 'Unnamed')}\n"
                f"  Relevance: {p.get('relevance', 'N/A')}\n"
                f"  Technologies: {', '.join(p.get('technologies', []))}\n"
                f"  Deployed: {'Yes ✓' if p.get('deployment_proof') else 'No'}"
                for p in extracted["projects"][:5]
            ])
            self.add_section(content_frame, row_idx, "🚀 Projects", projects_text, "#4facfe")
            row_idx += 1

        # Issues
        if extracted.get("issues"):
            issues_text = "\n".join([
                f"• [{i.get('type', 'N/A')}] {i.get('description', 'N/A')}" 
                for i in extracted["issues"]
            ])
            self.add_section(content_frame, row_idx, "⚡ Issues Detected", issues_text, "#f2994a")
            row_idx += 1

        # Close button
        close_btn = ctk.CTkButton(
            details_window, 
            text="Close", 
            command=details_window.destroy, 
            height=45, 
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=("#667eea", "#667eea"),
            hover_color=("#5568d3", "#5568d3")
        )
        close_btn.grid(row=2, column=0, padx=25, pady=(0, 25), sticky="ew")

    def add_section(self, parent, row, title, content, accent_color=None):
        """Add a styled section to the details view"""
        section_frame = ctk.CTkFrame(parent, corner_radius=12, border_width=2, border_color=("#e2e8f0", "#2d3748"))
        section_frame.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        section_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            section_frame, 
            text=title, 
            font=ctk.CTkFont(size=16, weight="bold"), 
            anchor="w"
        )
        title_label.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        if accent_color:
            title_label.configure(text_color=accent_color)

        # Content textbox
        content_box = ctk.CTkTextbox(
            section_frame, 
            font=ctk.CTkFont(size=13), 
            wrap="word", 
            height=100,
            corner_radius=8
        )
        content_box.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        content_box.insert("1.0", content)
        content_box.configure(state="disabled")

    def copy_to_clipboard(self, data):
        """Copy candidate details to clipboard"""
        try:
            text = f"CV: {os.path.basename(data.get('cv_file', ''))}\n"
            text += f"Score: {data.get('fit_score', '')}%\n"
            text += f"Recommendation: {data.get('recommendation', '')}\n\n"
            text += f"Summary:\n{data.get('summary', '')}\n"
            
            self.clipboard_clear()
            self.clipboard_append(text)
            self.show_toast("Copied to clipboard!", "success")
        except Exception as e:
            self.show_toast("Failed to copy", "error")

    # Appearance changer
    def change_appearance_mode(self, new_mode):
        """Change appearance mode"""
        ctk.set_appearance_mode(new_mode)
        self.show_toast(f"Theme changed to {new_mode}", "info")


if __name__ == "__main__":
    app = CVScannerApp()
    app.mainloop()
