import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from main import CVAnalyzer

# Appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CVScannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CV Analysis Tool")
        self.geometry("1100x800")
        # Grid configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Data
        self.analysis_data = {}
        self.results_widgets = []

        # Build UI
        self.create_sidebar()
        self.create_main_panel()

    # -----------------------
    # Sidebar
    # -----------------------
    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="CV Analysis\nTool", font=ctk.CTkFont(size=28, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Powered by AI",
            font=ctk.CTkFont(size=12),
            text_color=("gray70", "gray30"),
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 30))

        # CV Directory
        self.dir_label = ctk.CTkLabel(
            self.sidebar_frame, text="CV Directory", font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        )
        self.dir_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        self.dir_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Select folder...", height=40)
        self.dir_entry.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.browse_button = ctk.CTkButton(
            self.sidebar_frame,
            text="📁 Browse Folder",
            command=self.browse_directory,
            height=40,
            font=ctk.CTkFont(size=13),
        )
        self.browse_button.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Run
        self.run_button = ctk.CTkButton(
            self.sidebar_frame,
            text="▶ Run Analysis",
            command=self.run_analysis_thread,
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#1f6aa5", "#1f6aa5"),
            hover_color=("#144870", "#144870"),
        )
        self.run_button.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Progress
        self.progress = ctk.CTkProgressBar(self.sidebar_frame, mode="indeterminate")
        self.progress.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress.grid_remove()

        # Appearance selector
        self.appearance_label = ctk.CTkLabel(
            self.sidebar_frame, text="Appearance Mode:", anchor="w", font=ctk.CTkFont(size=12)
        )
        self.appearance_label.grid(row=7, column=0, padx=20, pady=(20, 5), sticky="w")

        self.appearance_mode = ctk.CTkOptionMenu(
            self.sidebar_frame, values=["System", "Dark", "Light"], command=self.change_appearance_mode, height=35
        )
        self.appearance_mode.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.appearance_mode.set("Dark")

        # Status
        self.status_label = ctk.CTkLabel(
            self.sidebar_frame, text="Ready", font=ctk.CTkFont(size=11), text_color=("gray60", "gray40"), anchor="w"
        )
        self.status_label.grid(row=9, column=0, padx=20, pady=(0, 20), sticky="sw")

    # -----------------------
    # Main panel
    # -----------------------
    def create_main_panel(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=2)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Job description
        self.jd_label = ctk.CTkLabel(
            self.main_frame, text="Job Description", font=ctk.CTkFont(size=18, weight="bold"), anchor="w"
        )
        self.jd_label.grid(row=0, column=0, padx=0, pady=(0, 10), sticky="w")

        self.jd_textbox = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(size=13), wrap="word", height=200)
        self.jd_textbox.grid(row=1, column=0, sticky="nsew", pady=(0, 20))

        # Results
        self.results_label = ctk.CTkLabel(
            self.main_frame, text="Top Candidates", font=ctk.CTkFont(size=18, weight="bold"), anchor="w"
        )
        self.results_label.grid(row=2, column=0, padx=0, pady=(10, 10), sticky="w")

        self.results_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="", corner_radius=10)
        self.results_frame.grid(row=3, column=0, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)

    # -----------------------
    # Directory & run
    # -----------------------
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, directory)
            self.update_status(f"📂 Selected: {os.path.basename(directory)}")

    def run_analysis_thread(self):
        cv_dir = self.dir_entry.get().strip()
        job_description = self.jd_textbox.get("1.0", "end").strip()

        if not cv_dir or not job_description:
            messagebox.showerror("Error", "Please provide both a CV directory and a job description.")
            return
        if not os.path.isdir(cv_dir):
            messagebox.showerror("Error", "The specified CV directory does not exist.")
            return

        # UI changes
        self.run_button.configure(state="disabled", text="⏳ Analyzing...")
        self.progress.grid()
        self.progress.start()
        self.update_status("🔄 Analysis in progress...")

        # Clear previous results
        for widget in self.results_widgets:
            try:
                widget.destroy()
            except Exception:
                pass
        self.results_widgets.clear()
        self.analysis_data.clear()

        # Start thread
        thread = threading.Thread(target=self.run_analysis, args=(cv_dir, job_description), daemon=True)
        thread.start()

    def run_analysis(self, cv_dir, job_description):
        try:
            analyzer = CVAnalyzer()
            all_results = analyzer.process_all_cvs(cv_dir, job_description)
            # store
            self.analysis_data = {os.path.basename(res["cv_file"]): res for res in all_results}
            top_candidates = analyzer.get_top_candidates(all_results, top_n=15)
            # update UI on main thread
            self.after(0, self.update_results, top_candidates)
        except Exception as e:
            self.after(0, lambda: self.show_error(f"An error occurred during analysis: {e}"))
        finally:
            self.after(0, self.analysis_complete)

    # -----------------------
    # Results UI
    # -----------------------
    def update_results(self, candidates):
        for widget in self.results_widgets:
            try:
                widget.destroy()
            except Exception:
                pass
        self.results_widgets.clear()

        if not candidates:
            no_results = ctk.CTkLabel(self.results_frame, text="No candidates found", font=ctk.CTkFont(size=14), text_color="gray")
            no_results.grid(row=0, column=0, pady=50)
            self.results_widgets.append(no_results)
            return

        for i, candidate in enumerate(candidates):
            card = self.create_candidate_card(self.results_frame, i, candidate)
            card.grid(row=i, column=0, padx=10, pady=8, sticky="ew")
            self.results_widgets.append(card)

    def create_candidate_card(self, parent, rank, candidate):
        rec = candidate.get("recommendation", "").upper()
        if "STRONG" in rec:
            border_color = ("#2ecc71", "#27ae60")
            rec_color = ("#2ecc71", "#27ae60")
        elif "GOOD" in rec:
            border_color = ("#3498db", "#2980b9")
            rec_color = ("#3498db", "#2980b9")
        else:
            border_color = ("#95a5a6", "#7f8c8d")
            rec_color = ("#95a5a6", "#7f8c8d")

        card_frame = ctk.CTkFrame(parent, corner_radius=10, border_width=2, border_color=border_color)
        card_frame.grid_columnconfigure(1, weight=1)

        rank_label = ctk.CTkLabel(
            card_frame, text=f"#{rank + 1}", font=ctk.CTkFont(size=20, weight="bold"), width=50, fg_color=border_color, corner_radius=8
        )
        rank_label.grid(row=0, column=0, rowspan=2, padx=15, pady=15, sticky="n")

        info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, columnspan=2, padx=(0, 15), pady=(15, 5), sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)

        name_label = ctk.CTkLabel(
            info_frame, text=os.path.basename(candidate.get("cv_file", "Unknown")), font=ctk.CTkFont(size=15, weight="bold"), anchor="w"
        )
        name_label.grid(row=0, column=0, sticky="w")

        score_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        score_frame.grid(row=1, column=1, padx=(0, 10), pady=(0, 15), sticky="w")

        fit_score_value = candidate.get("fit_score", 0)
        try:
            score_text = f"Score: {float(fit_score_value):.0f}%"
        except Exception:
            score_text = f"Score: {fit_score_value}"

        score_label = ctk.CTkLabel(score_frame, text=score_text, font=ctk.CTkFont(size=13), anchor="w")
        score_label.grid(row=0, column=0, padx=(0, 20))

        rec_badge = ctk.CTkLabel(
            score_frame,
            text=candidate.get("recommendation", ""),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white",
            fg_color=rec_color,
            corner_radius=6,
            padx=10,
            pady=5,
        )
        rec_badge.grid(row=0, column=1)

        details_btn = ctk.CTkButton(
            card_frame,
            text="View Details →",
            command=lambda c=candidate: self.show_cv_details_modern(c),
            width=120,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=border_color,
            hover_color=border_color,
        )
        details_btn.grid(row=1, column=2, padx=(0, 15), pady=(0, 15), sticky="e")

        return card_frame

    # -----------------------
    # Analysis complete / errors
    # -----------------------
    def analysis_complete(self):
        try:
            self.progress.stop()
            self.progress.grid_remove()
            self.run_button.configure(state="normal", text="▶ Run Analysis")
            self.update_status("✅ Analysis complete!")
            # Keep messagebox but don't let it steal things forever
            messagebox.showinfo("Success", "Analysis complete!")
        except Exception:
            pass

    def show_error(self, message):
        messagebox.showerror("Analysis Failed", message)
        self.update_status("❌ Analysis failed.")

    def update_status(self, message):
        # Keep it simple and safe to call from other threads via .after
        try:
            self.status_label.configure(text=message)
        except Exception:
            pass

    # -----------------------
    # Details popup (fixed focus behavior)
    # -----------------------
    def show_cv_details_modern(self, data):
        # Create top-level window
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"Analysis Details - {os.path.basename(data.get('cv_file',''))}")
        details_window.geometry("800x900")
        details_window.grid_columnconfigure(0, weight=1)
        details_window.grid_rowconfigure(1, weight=1)

        # Make it behave nicely: bring to front briefly then release topmost so user can interact normally
        try:
            details_window.transient(self)  # hint to OS this belongs to main window
            details_window.lift()
            details_window.attributes("-topmost", True)
            details_window.focus_force()
            # remove topmost flag shortly after so it doesn't permanently block other windows
            details_window.after(200, lambda: details_window.attributes("-topmost", False))
        except Exception:
            # On some platforms/versions flags may not be allowed; ignore if fails
            pass

        # Header
        header_frame = ctk.CTkFrame(details_window, corner_radius=0, height=80)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_propagate(False)

        title_label = ctk.CTkLabel(
            header_frame, text=os.path.basename(data.get("cv_file", "Unknown")), font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=30, pady=(20, 5), sticky="w")

        score_text = f"Fit Score: {data.get('fit_score', 'N/A')}% • {data.get('recommendation', '')}"
        score_label = ctk.CTkLabel(header_frame, text=score_text, font=ctk.CTkFont(size=13), text_color="gray")
        score_label.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

        # Scrollable content
        content_frame = ctk.CTkScrollableFrame(details_window)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        content_frame.grid_columnconfigure(0, weight=1)

        row_idx = 0

        if data.get("summary"):
            self.add_section(content_frame, row_idx, "📋 Overall Summary", data["summary"])
            row_idx += 1

        if data.get("strengths"):
            strengths_text = "\n".join([f"• {item}" for item in data["strengths"]])
            self.add_section(content_frame, row_idx, "✨ Key Strengths", strengths_text, "#2ecc71")
            row_idx += 1

        if data.get("gaps"):
            gaps_text = "\n".join([f"• {item}" for item in data["gaps"]])
            self.add_section(content_frame, row_idx, "⚠️ Potential Gaps", gaps_text, "#e74c3c")
            row_idx += 1

        if data.get("breakdown"):
            breakdown_text = "\n".join([f"• {item}" for item in data["breakdown"]])
            self.add_section(content_frame, row_idx, "📊 Score Breakdown", breakdown_text, "#3498db")
            row_idx += 1

        if data.get("note"):
            self.add_section(content_frame, row_idx, "📝 Additional Notes", data["note"])
            row_idx += 1

        # Close button
        close_btn = ctk.CTkButton(
            details_window, text="Close", command=details_window.destroy, height=40, font=ctk.CTkFont(size=14)
        )
        close_btn.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")

    def add_section(self, parent, row, title, content, accent_color=None):
        section_frame = ctk.CTkFrame(parent, corner_radius=10)
        section_frame.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        section_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            section_frame, text=title, font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        )
        title_label.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        if accent_color:
            title_label.configure(text_color=accent_color)

        # Content textbox (read-only)
        content_box = ctk.CTkTextbox(section_frame, font=ctk.CTkFont(size=13), wrap="word", height=100)
        content_box.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        content_box.insert("1.0", content)
        content_box.configure(state="disabled")

    # Appearance changer
    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)


if __name__ == "__main__":
    app = CVScannerApp()
    app.mainloop()
