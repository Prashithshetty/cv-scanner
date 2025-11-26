"""
Details Modal Component - Detailed candidate analysis view
"""

import customtkinter as ctk
import os
from .theme_manager import ThemeManager


class DetailsModal(ctk.CTkToplevel):
    """Modal window for displaying detailed candidate analysis"""
    
    def __init__(self, parent, candidate_data):
        super().__init__(parent)
        
        self.candidate_data = candidate_data
        
        # Window configuration
        self.title(f"Analysis Details - {os.path.basename(candidate_data.get('cv_file', ''))}")
        self.geometry("900x950")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Window behavior
        try:
            self.transient(parent)
            self.lift()
            self.attributes("-topmost", True)
            self.focus_force()
            self.after(200, lambda: self.attributes("-topmost", False))
        except:
            pass
        
        self._create_header()
        self._create_content()
        self._create_footer()
    
    def _create_header(self):
        """Create header with candidate info"""
        header_frame = ctk.CTkFrame(
            self,
            corner_radius=0,
            height=100,
            fg_color=("#667eea", "#5568d3")
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_propagate(False)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text=os.path.basename(self.candidate_data.get("cv_file", "Unknown")),
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#ffffff"
        )
        title_label.grid(row=0, column=0, padx=30, pady=(25, 5), sticky="w")
        
        # Score
        score_text = f"🎯 Match Score: {self.candidate_data.get('fit_score', 'N/A')}%  •  {self.candidate_data.get('recommendation', '')}"
        score_label = ctk.CTkLabel(
            header_frame,
            text=score_text,
            font=ThemeManager.get_font("body"),
            text_color="#ffffff"
        )
        score_label.grid(row=1, column=0, padx=30, pady=(0, 25), sticky="w")
        
        # Copy button
        copy_btn = ctk.CTkButton(
            header_frame,
            text="📋 Copy",
            command=self._copy_to_clipboard,
            width=90,
            height=35,
            corner_radius=8,
            fg_color="#ffffff",
            text_color=ThemeManager.COLORS["primary"],
            hover_color="#f0f0f0",
            font=ThemeManager.get_font("small_bold")
        )
        copy_btn.grid(row=0, column=1, rowspan=2, padx=30, pady=25, sticky="e")
    
    def _create_content(self):
        """Create scrollable content area"""
        content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=25)
        content_frame.grid_columnconfigure(0, weight=1)
        
        row_idx = 0
        
        # Summary
        if self.candidate_data.get("summary"):
            self._add_section(
                content_frame,
                row_idx,
                "📋 Overall Summary",
                self.candidate_data["summary"]
            )
            row_idx += 1
        
        # Score breakdown
        if self.candidate_data.get("breakdown"):
            breakdown_text = "\n".join(self.candidate_data["breakdown"])
            self._add_section(
                content_frame,
                row_idx,
                "📊 Score Breakdown",
                breakdown_text,
                ThemeManager.COLORS["primary"]
            )
            row_idx += 1
        
        # Skills analysis
        extracted = self.candidate_data.get("extracted_data", {})
        if extracted.get("required_skills"):
            found_skills = [s for s in extracted["required_skills"] if s.get("found")]
            missing_skills = [s for s in extracted["required_skills"] if not s.get("found")]
            
            if found_skills:
                skills_text = "\n".join([
                    f"✓ {s['skill']}: {s.get('evidence', 'N/A')[:100]}..."
                    for s in found_skills
                ])
                self._add_section(
                    content_frame,
                    row_idx,
                    "✨ Required Skills Found",
                    skills_text,
                    ThemeManager.COLORS["success"]
                )
                row_idx += 1
            
            if missing_skills:
                missing_text = "\n".join([f"✗ {s['skill']}" for s in missing_skills])
                self._add_section(
                    content_frame,
                    row_idx,
                    "⚠️ Missing Required Skills",
                    missing_text,
                    ThemeManager.COLORS["danger"]
                )
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
            self._add_section(
                content_frame,
                row_idx,
                "🚀 Projects",
                projects_text,
                ThemeManager.COLORS["info"]
            )
            row_idx += 1
        
        # Issues
        if extracted.get("issues"):
            issues_text = "\n".join([
                f"• [{i.get('type', 'N/A')}] {i.get('description', 'N/A')}"
                for i in extracted["issues"]
            ])
            self._add_section(
                content_frame,
                row_idx,
                "⚡ Issues Detected",
                issues_text,
                ThemeManager.COLORS["warning"]
            )
    
    def _create_footer(self):
        """Create footer with close button"""
        close_btn = ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            height=45,
            font=ThemeManager.get_font("body_bold"),
            **ThemeManager.get_button_style("primary")
        )
        close_btn.grid(row=2, column=0, padx=25, pady=(0, 25), sticky="ew")
    
    def _add_section(self, parent, row, title, content, accent_color=None):
        """Add a styled section"""
        section_frame = ctk.CTkFrame(
            parent,
            corner_radius=12,
            border_width=2,
            border_color=("#e2e8f0", "#2d3748")
        )
        section_frame.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        section_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=ThemeManager.get_font("subheading"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        if accent_color:
            title_label.configure(text_color=accent_color)
        
        content_box = ctk.CTkTextbox(
            section_frame,
            font=ThemeManager.get_font("body"),
            wrap="word",
            height=100,
            corner_radius=8
        )
        content_box.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        content_box.insert("1.0", content)
        content_box.configure(state="disabled")
    
    def _copy_to_clipboard(self):
        """Copy candidate details to clipboard"""
        try:
            text = f"CV: {os.path.basename(self.candidate_data.get('cv_file', ''))}\n"
            text += f"Score: {self.candidate_data.get('fit_score', '')}%\n"
            text += f"Recommendation: {self.candidate_data.get('recommendation', '')}\n\n"
            text += f"Summary:\n{self.candidate_data.get('summary', '')}\n"
            
            self.clipboard_clear()
            self.clipboard_append(text)
        except:
            pass
