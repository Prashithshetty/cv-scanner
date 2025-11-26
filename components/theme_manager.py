"""
Theme Manager - Centralized styling and colors for the CV Scanner GUI
"""

import customtkinter as ctk


class ThemeManager:
    """Manages themes, colors, and styling configurations"""
    
    # Color palettes
    COLORS = {
        "primary": "#667eea",
        "primary_dark": "#5568d3",
        "primary_darker": "#4451b8",
        "success": "#56ab2f",
        "success_dark": "#469024",
        "warning": "#f2994a",
        "danger": "#eb3349",
        "info": "#4facfe",
        "info_dark": "#3d8dce",
        "gray": "#a0aec0",
        "gray_dark": "#718096",
        "gray_light": "#e5e7eb",
        "border_light": "#d1d5db",
        "border_dark": "#2d3748",
    }
    
    # Gradient colors
    GRADIENTS = {
        "primary": ["#667eea", "#764ba2"],
        "success": ["#56ab2f", "#a8e063"],
        "warning": ["#f2994a", "#f2c94c"],
        "info": ["#4facfe", "#00f2fe"],
    }
    
    # Font configurations
    FONTS = {
        "title": ("Segoe UI", 32, "bold"),
        "heading": ("Segoe UI", 20, "bold"),
        "subheading": ("Segoe UI", 16, "bold"),
        "body": ("Segoe UI", 13),
        "body_bold": ("Segoe UI", 13, "bold"),
        "small": ("Segoe UI", 11),
        "small_bold": ("Segoe UI", 11, "bold"),
        "tiny": ("Segoe UI", 10),
    }
    
    # Component styles
    BUTTON_STYLES = {
        "primary": {
            "fg_color": COLORS["primary"],
            "hover_color": COLORS["primary_dark"],
            "text_color": "#ffffff",
            "corner_radius": 10,
        },
        "success": {
            "fg_color": COLORS["success"],
            "hover_color": COLORS["success_dark"],
            "text_color": "#ffffff",
            "corner_radius": 10,
        },
        "outline": {
            "fg_color": "transparent",
            "border_width": 2,
            "corner_radius": 10,
        },
    }
    
    CARD_STYLES = {
        "default": {
            "corner_radius": 12,
            "border_width": 2,
        },
        "elevated": {
            "corner_radius": 15,
            "border_width": 0,
        },
    }
    
    @staticmethod
    def get_color(color_name, light_mode=False):
        """Get color with support for light/dark modes"""
        return ThemeManager.COLORS.get(color_name, "#000000")
    
    @staticmethod
    def get_font(font_name):
        """Get font configuration"""
        font_config = ThemeManager.FONTS.get(font_name, ("Segoe UI", 13))
        return ctk.CTkFont(family=font_config[0], size=font_config[1], 
                          weight=font_config[2] if len(font_config) > 2 else "normal")
    
    @staticmethod
    def get_button_style(style_name):
        """Get button style configuration"""
        return ThemeManager.BUTTON_STYLES.get(style_name, {})
    
    @staticmethod
    def get_recommendation_color(recommendation):
        """Get color based on recommendation type"""
        rec_upper = recommendation.upper()
        if "SHORTLIST" in rec_upper:
            return ThemeManager.COLORS["success"]
        elif "REVIEW" in rec_upper:
            return ThemeManager.COLORS["info"]
        else:
            return ThemeManager.COLORS["gray"]
    
    @staticmethod
    def apply_theme(appearance_mode="dark"):
        """Apply global theme settings"""
        ctk.set_appearance_mode(appearance_mode)
        ctk.set_default_color_theme("blue")
