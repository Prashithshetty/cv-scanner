"""
Export Dialog Component - Export results to CSV or JSON
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import json
import csv
from datetime import datetime
from .theme_manager import ThemeManager


class ExportDialog(ctk.CTkToplevel):
    """Dialog for exporting analysis results"""
    
    def __init__(self, parent, candidates, stats):
        super().__init__(parent)
        
        self.candidates = candidates
        self.stats = stats
        
        # Window configuration
        self.title("Export Results")
        self.geometry("400x250")
        self.transient(parent)
        self.grab_set()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="📊 Export Analysis Results",
            font=ThemeManager.get_font("heading")
        )
        title.pack(pady=(20, 10))
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            self,
            text="Choose your export format",
            font=ThemeManager.get_font("small"),
            text_color=("#a0aec0", "#718096")
        )
        subtitle.pack(pady=(0, 20))
        
        # CSV button
        csv_btn = ctk.CTkButton(
            self,
            text="📄 Export as CSV",
            command=self._export_csv,
            height=45,
            font=ThemeManager.get_font("body_bold"),
            corner_radius=10,
            **ThemeManager.get_button_style("success")
        )
        csv_btn.pack(pady=5, padx=30, fill="x")
        
        # JSON button
        json_btn = ctk.CTkButton(
            self,
            text="📋 Export as JSON",
            command=self._export_json,
            height=45,
            font=ThemeManager.get_font("body_bold"),
            corner_radius=10,
            fg_color=ThemeManager.COLORS["info"],
            hover_color=ThemeManager.COLORS["info_dark"],
            text_color="#ffffff"
        )
        json_btn.pack(pady=5, padx=30, fill="x")
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            self,
            text="Cancel",
            command=self.destroy,
            height=40,
            font=ThemeManager.get_font("body"),
            corner_radius=10,
            fg_color="transparent",
            border_width=2,
            border_color=("#a0aec0", "#718096"),
            text_color=("#a0aec0", "#718096")
        )
        cancel_btn.pack(pady=(5, 20), padx=30, fill="x")
    
    def _export_csv(self):
        """Export results to CSV"""
        if not self.candidates:
            messagebox.showwarning("No Data", "No analysis data available to export.")
            self.destroy()
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
                
                for i, candidate in enumerate(self.candidates, 1):
                    writer.writerow([
                        i,
                        os.path.basename(candidate.get("cv_file", "")),
                        candidate.get("fit_score", ""),
                        candidate.get("recommendation", "")
                    ])
            
            messagebox.showinfo("Success", f"Results exported successfully to:\n{filename}")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export CSV:\n{str(e)}")
    
    def _export_json(self):
        """Export results to JSON"""
        if not self.candidates:
            messagebox.showwarning("No Data", "No analysis data available to export.")
            self.destroy()
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
                "total_candidates": len(self.candidates),
                "statistics": self.stats,
                "candidates": self.candidates
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Results exported successfully to:\n{filename}")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export JSON:\n{str(e)}")
