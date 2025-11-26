"""
Main Panel Component - Job description input and results display
"""

import customtkinter as ctk
from .theme_manager import ThemeManager
from .candidate_card import CandidateCard


class MainPanel(ctk.CTkFrame):
    """Main content panel with job description and results"""
    
    def __init__(self, parent, on_search_callback, on_sort_callback, on_filter_callback, on_export_callback, on_details_callback):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        
        self.on_search_callback = on_search_callback
        self.on_sort_callback = on_sort_callback
        self.on_filter_callback = on_filter_callback
        self.on_export_callback = on_export_callback
        self.on_details_callback = on_details_callback
        
        self.results_widgets = []
        
        # Grid configuration
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=2)
        self.grid_columnconfigure(0, weight=1)
        
        self._create_job_description_section()
        self._create_results_header()
        self._create_results_display()
    
    def _create_job_description_section(self):
        """Create job description input section"""
        # Header
        jd_header = ctk.CTkFrame(self, fg_color="transparent")
        jd_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        jd_header.grid_columnconfigure(0, weight=1)
        
        jd_label = ctk.CTkLabel(
            jd_header,
            text="📝 Job Description",
            font=ThemeManager.get_font("heading"),
            anchor="w"
        )
        jd_label.grid(row=0, column=0, sticky="w")
        
        self.char_count_label = ctk.CTkLabel(
            jd_header,
            text="0 characters",
            font=ThemeManager.get_font("small"),
            text_color=("#6b7280", "#718096"),
            anchor="e"
        )
        self.char_count_label.grid(row=0, column=1, sticky="e")
        
        # Textbox
        self.jd_textbox = ctk.CTkTextbox(
            self,
            font=ThemeManager.get_font("body"),
            wrap="word",
            height=200,
            corner_radius=12,
            border_width=2,
            border_color=("#d1d5db", "#2d3748")
        )
        self.jd_textbox.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        self.jd_textbox.bind("<KeyRelease>", self._update_char_count)
    
    def _create_results_header(self):
        """Create results header with controls"""
        results_header = ctk.CTkFrame(self, fg_color="transparent")
        results_header.grid(row=2, column=0, sticky="ew", pady=(10, 10))
        results_header.grid_columnconfigure(1, weight=1)
        
        results_label = ctk.CTkLabel(
            results_header,
            text="🏆 Top Candidates",
            font=ThemeManager.get_font("heading"),
            anchor="w"
        )
        results_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        # Search
        self.search_entry = ctk.CTkEntry(
            results_header,
            placeholder_text="🔍 Search candidates...",
            height=36,
            width=200,
            corner_radius=8
        )
        self.search_entry.grid(row=0, column=1, sticky="e", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.on_search_callback())
        
        # Sort menu
        self.sort_menu = ctk.CTkOptionMenu(
            results_header,
            values=["Sort: Score ↓", "Sort: Name ↑", "Sort: Name ↓"],
            command=self.on_sort_callback,
            height=36,
            width=140,
            corner_radius=8,
            fg_color=("#4c51bf", "#667eea"),
            button_color=("#434190", "#5568d3"),
            button_hover_color=("#3c366b", "#4451b8")
        )
        self.sort_menu.grid(row=0, column=2, sticky="e", padx=(0, 10))
        self.sort_menu.set("Sort: Score ↓")
        
        # Filter menu
        self.filter_menu = ctk.CTkOptionMenu(
            results_header,
            values=["All", "Shortlist", "Review", "Other"],
            command=self.on_filter_callback,
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
        export_btn = ctk.CTkButton(
            results_header,
            text="💾 Export",
            command=self.on_export_callback,
            height=36,
            width=100,
            font=ThemeManager.get_font("body_bold"),
            **ThemeManager.get_button_style("success")
        )
        export_btn.grid(row=0, column=4, sticky="e")
    
    def _create_results_display(self):
        """Create scrollable results display"""
        self.results_frame = ctk.CTkScrollableFrame(
            self,
            label_text="",
            corner_radius=12,
            fg_color=("#f3f4f6", "#1a202c"),
            border_width=2,
            border_color=("#e5e7eb", "#2d3748")
        )
        self.results_frame.grid(row=3, column=0, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
    
    def _update_char_count(self, event=None):
        """Update character count"""
        content = self.jd_textbox.get("1.0", "end-1c")
        char_count = len(content)
        self.char_count_label.configure(text=f"{char_count} characters")
    
    # Public methods
    def get_job_description(self):
        """Get job description text"""
        return self.jd_textbox.get("1.0", "end").strip()
    
    def get_search_query(self):
        """Get search query"""
        return self.search_entry.get().lower()
    
    def display_results(self, candidates):
        """Display candidate results"""
        # Clear previous results
        for widget in self.results_widgets:
            try:
                widget.destroy()
            except:
                pass
        self.results_widgets.clear()
        
        if not candidates:
            no_results = ctk.CTkLabel(
                self.results_frame,
                text="No candidates found matching the criteria",
                font=ThemeManager.get_font("subheading"),
                text_color=("#6b7280", "#718096")
            )
            no_results.grid(row=0, column=0, pady=50)
            self.results_widgets.append(no_results)
            return
        
        # Create candidate cards
        for i, candidate in enumerate(candidates):
            card = CandidateCard(
                self.results_frame,
                i,
                candidate,
                self.on_details_callback
            )
            card.grid(row=i, column=0, padx=0, pady=6, sticky="ew")
            self.results_widgets.append(card)
    
    def clear_results(self):
        """Clear all results"""
        for widget in self.results_widgets:
            try:
                widget.destroy()
            except:
                pass
        self.results_widgets.clear()
