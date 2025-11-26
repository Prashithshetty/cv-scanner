"""
Sidebar Component - Left sidebar with controls and settings
"""

import customtkinter as ctk
from tkinter import filedialog
import os
from .theme_manager import ThemeManager


class Sidebar(ctk.CTkFrame):
    """Sidebar component with directory selection, analysis controls, and settings"""
    
    def __init__(self, parent, on_browse_callback, on_run_callback, on_appearance_change):
        super().__init__(parent, width=300, corner_radius=0, fg_color=("#f8f9fa", "#16213e"))
        
        self.on_browse_callback = on_browse_callback
        self.on_run_callback = on_run_callback
        self.on_appearance_change = on_appearance_change
        
        # Settings
        self.parallel_workers = 3
        self.enable_summaries = False
        
        # Setup UI
        self.grid_propagate(False)
        self.grid_rowconfigure(7, weight=1)
        
        self._create_header()
        self._create_directory_section()
        self._create_run_button()
        self._create_progress_section()
        self._create_stats_section()
        self._create_performance_section()
        self._create_appearance_selector()
        self._create_status_label()
    
    def _create_header(self):
        """Create header with logo and subtitle"""
        # Logo frame
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(30, 5), sticky="ew")
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="CV Scanner",
            font=ThemeManager.get_font("title"),
            text_color=("#5568d3", "#667eea")
        )
        logo_label.pack()
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            self,
            text="✨ AI-Powered Analysis",
            font=ThemeManager.get_font("small"),
            text_color=("#6b7280", "#a0aec0")
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 30))
        
        # Divider
        divider = ctk.CTkFrame(self, height=2, fg_color=("#e5e7eb", "#2d3748"))
        divider.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
    
    def _create_directory_section(self):
        """Create CV directory selection section"""
        # Label
        label = ctk.CTkLabel(
            self,
            text="📂 CV Directory",
            font=ThemeManager.get_font("subheading"),
            anchor="w"
        )
        label.grid(row=3, column=0, padx=20, pady=(0, 8), sticky="w")
        
        # Entry
        self.dir_entry = ctk.CTkEntry(
            self,
            placeholder_text="Select folder with CVs...",
            height=42,
            corner_radius=10,
            border_width=2,
            border_color=("#d1d5db", "#2d3748")
        )
        self.dir_entry.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Browse button
        self.browse_btn = ctk.CTkButton(
            self,
            text="📁 Browse Folder",
            command=self._on_browse_clicked,
            height=42,
            font=ThemeManager.get_font("body_bold"),
            **ThemeManager.get_button_style("primary")
        )
        self.browse_btn.grid(row=5, column=0, padx=20, pady=(0, 25), sticky="ew")
    
    def _create_run_button(self):
        """Create main run analysis button"""
        self.run_btn = ctk.CTkButton(
            self,
            text="🚀 Start Analysis",
            command=self._on_run_clicked,
            height=55,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=12,
            fg_color="transparent",
            border_width=2,
            border_color=("#667eea", "#667eea"),
            text_color=("#5568d3", "#ffffff"),
            hover_color=("#e0e7ff", "#667eea")
        )
        self.run_btn.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="ew")
    
    def _create_progress_section(self):
        """Create progress indicator section"""
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="new")
        self.progress_frame.grid_remove()
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Processing...",
            font=ThemeManager.get_font("small"),
            text_color=("#6b7280", "#a0aec0")
        )
        self.progress_label.pack(pady=(0, 5))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            mode="determinate",
            height=8
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        
        self.progress_percent = ctk.CTkLabel(
            self.progress_frame,
            text="0%",
            font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.COLORS["primary"]
        )
        self.progress_percent.pack(pady=(5, 0))
        
        # Time estimate label
        self.time_estimate_label = ctk.CTkLabel(
            self.progress_frame,
            text="Estimating time...",
            font=ThemeManager.get_font("tiny"),
            text_color=("#9ca3af", "#6b7280")
        )
        self.time_estimate_label.pack(pady=(3, 0))
    
    def _create_stats_section(self):
        """Create statistics display section"""
        self.stats_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=("#ffffff", "#0f1419")
        )
        self.stats_frame.grid(row=8, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.stats_frame.grid_remove()
        
        stats_title = ctk.CTkLabel(
            self.stats_frame,
            text="📊 Analysis Stats",
            font=ThemeManager.get_font("small_bold")
        )
        stats_title.pack(pady=(10, 5))
        
        self.stats_text = ctk.CTkLabel(
            self.stats_frame,
            text="",
            font=ThemeManager.get_font("small"),
            justify="left"
        )
        self.stats_text.pack(pady=(0, 10), padx=10)
    
    def _create_performance_section(self):
        """Create performance settings section"""
        # Divider
        divider = ctk.CTkFrame(self, height=2, fg_color=("#e5e7eb", "#2d3748"))
        divider.grid(row=9, column=0, sticky="ew", padx=20, pady=(0, 15))
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="⚡ Performance",
            anchor="w",
            font=ThemeManager.get_font("small_bold")
        )
        title.grid(row=10, column=0, padx=20, pady=(0, 8), sticky="w")
        
        # Workers slider
        workers_frame = ctk.CTkFrame(self, fg_color="transparent")
        workers_frame.grid(row=11, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        workers_label = ctk.CTkLabel(
            workers_frame,
            text="Parallel Workers:",
            font=ThemeManager.get_font("small"),
            anchor="w"
        )
        workers_label.pack(side="left")
        
        self.workers_value_label = ctk.CTkLabel(
            workers_frame,
            text="3",
            font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.COLORS["primary"],
            anchor="e"
        )
        self.workers_value_label.pack(side="right")
        
        self.workers_slider = ctk.CTkSlider(
            self,
            from_=1,
            to=6,
            number_of_steps=5,
            command=self._on_workers_changed,
            height=16,
            button_color=ThemeManager.COLORS["primary"],
            button_hover_color=ThemeManager.COLORS["primary_dark"],
            progress_color=ThemeManager.COLORS["primary"]
        )
        self.workers_slider.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.workers_slider.set(3)
        
        # Summary toggle
        summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        summary_frame.grid(row=13, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        summary_label = ctk.CTkLabel(
            summary_frame,
            text="AI Summaries:",
            font=ThemeManager.get_font("small"),
            anchor="w"
        )
        summary_label.pack(side="left")
        
        self.summary_switch = ctk.CTkSwitch(
            summary_frame,
            text="",
            command=self._on_summary_toggled,
            width=40,
            height=20,
            button_color=ThemeManager.COLORS["primary"],
            button_hover_color=ThemeManager.COLORS["primary_dark"],
            progress_color=ThemeManager.COLORS["primary"]
        )
        self.summary_switch.pack(side="right")
        self.summary_switch.deselect()
    
    def _create_appearance_selector(self):
        """Create theme appearance selector"""
        label = ctk.CTkLabel(
            self,
            text="🎨 Theme",
            anchor="w",
            font=ThemeManager.get_font("small_bold")
        )
        label.grid(row=14, column=0, padx=20, pady=(10, 8), sticky="w")
        
        self.appearance_menu = ctk.CTkOptionMenu(
            self,
            values=["Dark", "Light", "System"],
            command=self.on_appearance_change,
            height=38,
            corner_radius=10,
            fg_color=ThemeManager.COLORS["primary"],
            button_color=ThemeManager.COLORS["primary_dark"],
            button_hover_color=ThemeManager.COLORS["primary_darker"]
        )
        self.appearance_menu.grid(row=15, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.appearance_menu.set("Dark")
    
    def _create_status_label(self):
        """Create status label at bottom"""
        self.status_label = ctk.CTkLabel(
            self,
            text="✓ Ready to analyze",
            font=ThemeManager.get_font("small"),
            text_color=ThemeManager.COLORS["success"],
            anchor="w"
        )
        self.status_label.grid(row=16, column=0, padx=20, pady=(10, 25), sticky="sw")
    
    # Event handlers
    def _on_browse_clicked(self):
        """Handle browse button click"""
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, directory)
            self.on_browse_callback(directory)
    
    def _on_run_clicked(self):
        """Handle run button click"""
        cv_dir = self.dir_entry.get().strip()
        if cv_dir:
            self.on_run_callback(cv_dir)
    
    def _on_workers_changed(self, value):
        """Handle workers slider change"""
        self.parallel_workers = int(value)
        self.workers_value_label.configure(text=str(self.parallel_workers))
    
    def _on_summary_toggled(self):
        """Handle summary switch toggle"""
        self.enable_summaries = bool(self.summary_switch.get())
    
    # Public methods
    def get_directory(self):
        """Get selected directory"""
        return self.dir_entry.get().strip()
    
    def get_settings(self):
        """Get performance settings"""
        return {
            "parallel_workers": self.parallel_workers,
            "enable_summaries": self.enable_summaries
        }
    
    def set_status(self, message, color=None):
        """Update status label"""
        self.status_label.configure(text=message)
        if color:
            self.status_label.configure(text_color=color)
    
    def show_progress(self, show=True):
        """Show or hide progress indicator"""
        if show:
            self.progress_frame.grid()
            self.progress_bar.set(0)
            self.progress_percent.configure(text="0%")
            self.time_estimate_label.configure(text="Estimating time...")
        else:
            self.progress_frame.grid_remove()
    
    def update_progress(self, current, total, elapsed_time=0):
        """Update progress bar with percentage and time estimate"""
        if total == 0:
            return
        
        progress = current / total
        percent = int(progress * 100)
        
        # Update progress bar and percentage
        self.progress_bar.set(progress)
        self.progress_percent.configure(text=f"{percent}%")
        
        # Calculate time estimate
        if current > 0 and elapsed_time > 0:
            avg_time_per_item = elapsed_time / current
            remaining_items = total - current
            estimated_remaining = avg_time_per_item * remaining_items
            
            # Format time estimate
            if estimated_remaining < 60:
                time_str = f"~{int(estimated_remaining)}s remaining"
            elif estimated_remaining < 3600:
                minutes = int(estimated_remaining / 60)
                seconds = int(estimated_remaining % 60)
                time_str = f"~{minutes}m {seconds}s remaining"
            else:
                hours = int(estimated_remaining / 3600)
                minutes = int((estimated_remaining % 3600) / 60)
                time_str = f"~{hours}h {minutes}m remaining"
            
            self.time_estimate_label.configure(text=time_str)
            self.progress_label.configure(text=f"Processing {current}/{total} CVs...")
        else:
            self.time_estimate_label.configure(text="Calculating...")
            self.progress_label.configure(text=f"Processing {current}/{total} CVs...")
    
    def set_run_button_state(self, analyzing=False):
        """Update run button state"""
        if analyzing:
            self.run_btn.configure(
                state="disabled",
                text="⏳ Analyzing...",
                fg_color=ThemeManager.COLORS["primary"],
                text_color="#ffffff"
            )
        else:
            self.run_btn.configure(
                state="normal",
                text="🚀 Start Analysis",
                fg_color="transparent",
                text_color=("#5568d3", "#ffffff")
            )
    
    def show_stats(self, stats):
        """Display analysis statistics"""
        self.stats_frame.grid()
        stats_text = (
            f"Total: {stats['total']}\n"
            f"✓ Shortlist: {stats['shortlist']}\n"
            f"● Review: {stats['review']}\n"
            f"✗ Other: {stats.get('reject', 0)}"
        )
        self.stats_text.configure(text=stats_text)
    
    def hide_stats(self):
        """Hide statistics section"""
        self.stats_frame.grid_remove()
