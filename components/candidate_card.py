"""
Candidate Card Component - Individual candidate result card
"""

import customtkinter as ctk
import os
from .theme_manager import ThemeManager


class CandidateCard(ctk.CTkFrame):
    """Modern candidate card with score, recommendation, and details button"""
    
    def __init__(self, parent, rank, candidate_data, on_details_callback):
        # Determine colors based on recommendation
        rec = candidate_data.get("recommendation", "").upper()
        if "SHORTLIST" in rec:
            border_color = ThemeManager.COLORS["success"]
            rank_bg = ThemeManager.COLORS["success"]
        elif "REVIEW" in rec:
            border_color = ThemeManager.COLORS["info"]
            rank_bg = ThemeManager.COLORS["info"]
        else:
            border_color = ThemeManager.COLORS["gray"]
            rank_bg = ThemeManager.COLORS["gray_dark"]
        
        super().__init__(
            parent,
            corner_radius=12,
            border_width=2,
            border_color=border_color,
            fg_color=("#ffffff", "#1e2433")
        )
        
        self.candidate_data = candidate_data
        self.on_details_callback = on_details_callback
        self.border_color = border_color
        self.rank_bg = rank_bg
        
        self.grid_columnconfigure(1, weight=1)
        
        self._create_rank_badge(rank)
        self._create_info_section()
        self._create_score_section()
        self._create_skills_section()
        self._create_details_button()
    
    def _create_rank_badge(self, rank):
        """Create rank badge"""
        rank_label = ctk.CTkLabel(
            self,
            text=f"#{rank + 1}",
            font=ctk.CTkFont(size=22, weight="bold"),
            width=60,
            height=60,
            fg_color=self.rank_bg,
            corner_radius=10,
            text_color="#ffffff"
        )
        rank_label.grid(row=0, column=0, rowspan=2, padx=15, pady=15, sticky="n")
    
    def _create_info_section(self):
        """Create name and basic info"""
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, columnspan=2, padx=(0, 15), pady=(15, 5), sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Name
        name_text = os.path.basename(self.candidate_data.get("cv_file", "Unknown"))
        if len(name_text) > 50:
            name_text = name_text[:47] + "..."
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=name_text,
            font=ThemeManager.get_font("subheading"),
            anchor="w"
        )
        name_label.grid(row=0, column=0, sticky="w")
    
    def _create_score_section(self):
        """Create score bar and recommendation badge"""
        score_frame = ctk.CTkFrame(self, fg_color="transparent")
        score_frame.grid(row=1, column=1, padx=(0, 10), pady=(0, 15), sticky="w")
        
        # Score
        fit_score_value = self.candidate_data.get("fit_score", 0)
        try:
            score_num = float(fit_score_value)
            score_text = f"Match: {score_num:.0f}%"
        except:
            score_num = 0
            score_text = f"Match: {fit_score_value}"
        
        score_container = ctk.CTkFrame(score_frame, fg_color="transparent")
        score_container.grid(row=0, column=0, sticky="w")
        
        score_label = ctk.CTkLabel(
            score_container,
            text=score_text,
            font=ThemeManager.get_font("body_bold"),
            anchor="w"
        )
        score_label.pack(anchor="w", pady=(0, 3))
        
        # Score bar
        score_bar_bg = ctk.CTkFrame(
            score_container,
            height=6,
            width=150,
            corner_radius=3,
            fg_color=("#e2e8f0", "#2d3748")
        )
        score_bar_bg.pack(anchor="w")
        
        try:
            bar_width = int((score_num / 100) * 150)
            score_bar = ctk.CTkFrame(
                score_bar_bg,
                height=6,
                width=bar_width,
                corner_radius=3,
                fg_color=self.border_color
            )
            score_bar.place(x=0, y=0)
        except:
            pass
        
        # Recommendation badge
        rec_badge = ctk.CTkLabel(
            score_frame,
            text=self.candidate_data.get("recommendation", "N/A"),
            font=ThemeManager.get_font("small_bold"),
            text_color="#ffffff",
            fg_color=self.border_color,
            corner_radius=8,
            padx=12,
            pady=6
        )
        rec_badge.grid(row=0, column=1, padx=(15, 0))
    
    def _create_skills_section(self):
        """Create skills tags if available"""
        extracted = self.candidate_data.get("extracted_data", {})
        if extracted.get("required_skills"):
            found_skills = [s for s in extracted["required_skills"] if s.get("found")][:3]
            if found_skills:
                skills_frame = ctk.CTkFrame(self, fg_color="transparent")
                skills_frame.grid(row=2, column=1, padx=(0, 10), pady=(0, 12), sticky="w")
                
                for idx, skill in enumerate(found_skills):
                    skill_tag = ctk.CTkLabel(
                        skills_frame,
                        text=f"✓ {skill['skill'][:15]}",
                        font=ThemeManager.get_font("tiny"),
                        fg_color=("#e6ffed", "#1a3d2e"),
                        text_color=("#22863a", "#56ab2f"),
                        corner_radius=5,
                        padx=8,
                        pady=3
                    )
                    skill_tag.grid(row=0, column=idx, padx=(0, 5))
    
    def _create_details_button(self):
        """Create view details button"""
        details_btn = ctk.CTkButton(
            self,
            text="View Details →",
            command=lambda: self.on_details_callback(self.candidate_data),
            width=130,
            height=36,
            font=ThemeManager.get_font("body_bold"),
            corner_radius=8,
            fg_color="transparent",
            border_width=2,
            border_color=self.border_color,
            text_color=self.border_color,
            hover_color=self.border_color
        )
        details_btn.grid(row=1, column=2, rowspan=2, padx=(0, 15), pady=(0, 15), sticky="e")
