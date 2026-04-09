#!/usr/bin/env python3
"""
TELE-Vir Status GUI Application

Displays all available databases, host genomes, and software from sources.yaml
with their installation status from utility_local.db.
"""

import os
import sys
import sqlite3
import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from load_sources import list_databases, list_software, list_hosts
from config import DATABASE_FILENAME
from install_source import ENVS_PARAMS

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class TelevirStatusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TELE-Vir Status")
        self.geometry("1200x800")
        
        self.install_home = os.environ.get('INSTALL_HOME', '/opt/televir')
        self.db_path = os.path.join(self.install_home, DATABASE_FILENAME)
        self.env_root = os.path.join(self.install_home, "envs")
        
        self.ARCHIVE_INSTALL_PATHS = {
            "clark": "classification/Clark",
            "voyager": "classification/Voyager/voyager-cli",
            "trimmomatic": "trimmomatic",
            "fastqc": "fastqc",
            "rabbitqc": "RabbitQC",
        }
        
        self.GIT_INSTALL_PATHS = {
            "fastviromeexplorer": "FastViromeExplorer",
            "desamba": "classm_lc/deSAMBA",
            "rabbitqc_git": "RabbitQC",
            "trimmomatic_git": "trimmomatic",
        }
        
        self._create_widgets()
        self._populate_all()
        
        self.after(100, self._apply_row_colors)
    
    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        title_frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            title_frame,
            text="TELE-Vir Status",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")
        
        self.refresh_btn = ctk.CTkButton(
            title_frame,
            text="↻ Refresh",
            command=self._populate_all,
            width=120,
            height=36,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.refresh_btn.grid(row=0, column=1, sticky="e")
        
        self.export_btn = ctk.CTkButton(
            title_frame,
            text="Export TSV",
            command=self.export_tsv,
            width=120,
            height=36,
            font=ctk.CTkFont(size=14)
        )
        self.export_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))
        
        self.tabview = ctk.CTkTabview(self, fg_color="transparent")
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.tabview.grid_columnconfigure(0, weight=1)
        
        self.tab_db = self.tabview.add("Databases")
        self.tab_hosts = self.tabview.add("Host Genomes")
        self.tab_soft = self.tabview.add("Software")
        
        self._create_databases_tab()
        self._create_hosts_tab()
        self._create_software_tab()
    
    def _create_databases_tab(self):
        self.tab_db.grid_rowconfigure(0, weight=1)
        self.tab_db.grid_columnconfigure(0, weight=1)
        
        container = ctk.CTkFrame(self.tab_db, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        scrollable = ctk.CTkScrollableFrame(
            container,
            label_text="Databases",
            label_font=ctk.CTkFont(size=16, weight="bold")
        )
        scrollable.grid(row=0, column=0, sticky="nsew")
        
        headers = ["Name", "Category", "Description", "Available", "Installed", "Version", "Date"]
        widths = [180, 100, 220, 90, 90, 100, 100]
        
        header_frame = ctk.CTkFrame(scrollable, fg_color="#2B2B2B", corner_radius=0)
        header_frame.pack(fill="x", pady=(0, 2))
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=13, weight="bold"),
                width=width,
                anchor="w"
            )
            label.pack(side="left", padx=8, pady=8)
        
        self.db_rows_frame = ctk.CTkFrame(scrollable, fg_color="transparent")
        self.db_rows_frame.pack(fill="both", expand=True)
    
    def _create_hosts_tab(self):
        self.tab_hosts.grid_rowconfigure(0, weight=1)
        self.tab_hosts.grid_columnconfigure(0, weight=1)
        
        container = ctk.CTkFrame(self.tab_hosts, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        scrollable = ctk.CTkScrollableFrame(
            container,
            label_text="Host Genomes",
            label_font=ctk.CTkFont(size=16, weight="bold")
        )
        scrollable.grid(row=0, column=0, sticky="nsew")
        
        headers = ["Name", "Common Name", "Available", "Installed", "Filename"]
        widths = [150, 120, 100, 100, 200]
        
        header_frame = ctk.CTkFrame(scrollable, fg_color="#2B2B2B", corner_radius=0)
        header_frame.pack(fill="x", pady=(0, 2))
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=13, weight="bold"),
                width=width,
                anchor="w"
            )
            label.pack(side="left", padx=8, pady=8)
        
        self.host_rows_frame = ctk.CTkFrame(scrollable, fg_color="transparent")
        self.host_rows_frame.pack(fill="both", expand=True)
    
    def _create_software_tab(self):
        self.tab_soft.grid_rowconfigure(0, weight=1)
        self.tab_soft.grid_columnconfigure(0, weight=1)
        
        container = ctk.CTkFrame(self.tab_soft, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        scrollable = ctk.CTkScrollableFrame(
            container,
            label_text="Software",
            label_font=ctk.CTkFont(size=16, weight="bold")
        )
        scrollable.grid(row=0, column=0, sticky="nsew")
        
        headers = ["Name", "Type", "Available", "Installed", "Tag"]
        widths = [200, 100, 100, 100, 150]
        
        header_frame = ctk.CTkFrame(scrollable, fg_color="#2B2B2B", corner_radius=0)
        header_frame.pack(fill="x", pady=(0, 2))
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=13, weight="bold"),
                width=width,
                anchor="w"
            )
            label.pack(side="left", padx=8, pady=8)
        
        self.soft_rows_frame = ctk.CTkFrame(scrollable, fg_color="transparent")
        self.soft_rows_frame.pack(fill="both", expand=True)
    
    def _populate_all(self):
        self._populate_databases()
        self._populate_hosts()
        self._populate_software()
        self._apply_row_colors()
    
    def _populate_databases(self):
        for widget in self.db_rows_frame.winfo_children():
            widget.destroy()
        
        dbs = list_databases()
        installed_dbs = self._get_installed_databases()
        
        row_idx = 0
        for category, entries in dbs.items():
            if isinstance(entries, dict):
                for name, info in entries.items():
                    name_full = f"{category}/{name}"
                    available = "✓" if info else "✗"
                    description = installed_dbs.get(name_full, {}).get("description", "N/A")
                    version = installed_dbs.get(name_full, {}).get("version", "N/A")
                    installed = installed_dbs.get(name_full, {}).get("installed", "N/A")
                    date = installed_dbs.get(name_full, {}).get("date", "N/A")
                    is_installed = installed == "True"
                    
                    self._add_db_row(
                        name_full, category, description, available,
                        installed, version, date, is_installed
                    )
                    row_idx += 1
    
    def _add_db_row(self, name, category, description, available, installed, version, date, is_installed):
        colors = ("#1E3A1E", "#2B2B2B") if hasattr(self, '_row_idx') else ("#2B2B2B", "#1E3A1E")
        self.db_rows_frame._row_idx = getattr(self.db_rows_frame, '_row_idx', 0) + 1
        
        bg = "#2B2B2B" if self.db_rows_frame._row_idx % 2 == 0 else "#1E3A1E" if is_installed else "#252525"
        
        frame = ctk.CTkFrame(self.db_rows_frame, fg_color=bg, corner_radius=4)
        frame.pack(fill="x", pady=2)
        
        values = [
            (name, 180), (category, 100), (description, 220),
            (available, 90), (installed, 90), (version, 100), (date, 100)
        ]
        
        for val, width in values:
            color = "#4ADE80" if val == "✓" else "#F87171" if val == "✗" else "#FFFFFF"
            label = ctk.CTkLabel(
                frame,
                text=val,
                font=ctk.CTkFont(size=12),
                width=width,
                anchor="w"
            )
            label.pack(side="left", padx=8, pady=6)
    
    def _populate_hosts(self):
        for widget in self.host_rows_frame.winfo_children():
            widget.destroy()
        
        hosts = list_hosts()
        installed_hosts = self._get_installed_hosts()
        
        for key, info in hosts.items():
            if isinstance(info, dict):
                host_name = info.get('host_name', key)
                common = info.get('common_name', 'N/A')
                available = "✓" if info else "✗"
                filename = "N/A"
                installed = "✗"
                for display_name, fn in installed_hosts.items():
                    if host_name.lower() in display_name.lower():
                        filename = fn
                        installed = "✓"
                        break
                is_installed = installed == "✓"
                self._add_host_row(host_name, common, available, installed, filename, is_installed)
    
    def _add_host_row(self, name, common_name, available, installed, filename, is_installed):
        bg = "#2B2B2B" if getattr(self, '_host_row_idx', 0) % 2 == 0 else "#1E3A1E" if is_installed else "#252525"
        self._host_row_idx = getattr(self, '_host_row_idx', 0) + 1
        
        frame = ctk.CTkFrame(self.host_rows_frame, fg_color=bg, corner_radius=4)
        frame.pack(fill="x", pady=2)
        
        values = [
            (name, 150), (common_name, 120), (available, 100),
            (installed, 100), (filename, 200)
        ]
        
        for val, width in values:
            color = "#4ADE80" if val == "✓" else "#F87171" if val == "✗" else "#FFFFFF"
            label = ctk.CTkLabel(
                frame,
                text=val,
                font=ctk.CTkFont(size=12),
                width=width,
                anchor="w"
            )
            label.pack(side="left", padx=8, pady=6)
    
    def _populate_software(self):
        for widget in self.soft_rows_frame.winfo_children():
            widget.destroy()
        
        soft = list_software()
        installed_soft = self._get_installed_software()
        
        row_idx = 0
        for name, info in soft.get('archives', {}).items():
            if info and isinstance(info, dict):
                available = "✓" if self._check_archive_installed(name, info) else "✗"
                tag = installed_soft.get(name, "N/A")
                installed = "✓" if tag != "N/A" else "✗"
                is_installed = installed == "✓"
                self._add_soft_row(name, "archive", available, installed, tag, is_installed)
                row_idx += 1
        
        for name, info in soft.get('git_repos', {}).items():
            if info and isinstance(info, dict):
                available = "✓" if self._check_git_installed(name, info) else "✗"
                tag = installed_soft.get(name, "N/A")
                installed = "✓" if tag != "N/A" else "✗"
                is_installed = installed == "✓"
                self._add_soft_row(name, "git", available, installed, tag, is_installed)
                row_idx += 1
        
        for name, info in soft.get('conda_tools', {}).items():
            if info and isinstance(info, dict):
                yaml_file = info.get('yaml', '')
                binary_name = info.get('binary', name)
                available = "✓" if self._check_conda_binary(yaml_file, binary_name) else "✗"
                tag = installed_soft.get(name, "N/A")
                installed = "✓" if tag != "N/A" else "✗"
                is_installed = installed == "✓"
                self._add_soft_row(name, "conda", available, installed, tag, is_installed)
                row_idx += 1
    
    def _add_soft_row(self, name, s_type, available, installed, tag, is_installed):
        bg = "#2B2B2B" if getattr(self, '_soft_row_idx', 0) % 2 == 0 else "#1E3A1E" if is_installed else "#252525"
        self._soft_row_idx = getattr(self, '_soft_row_idx', 0) + 1
        
        frame = ctk.CTkFrame(self.soft_rows_frame, fg_color=bg, corner_radius=4)
        frame.pack(fill="x", pady=2)
        
        values = [
            (name, 200), (s_type, 100), (available, 100),
            (installed, 100), (tag, 150)
        ]
        
        for val, width in values:
            color = "#4ADE80" if val == "✓" else "#F87171" if val == "✗" else "#FFFFFF"
            label = ctk.CTkLabel(
                frame,
                text=val,
                font=ctk.CTkFont(size=12),
                width=width,
                anchor="w"
            )
            label.pack(side="left", padx=8, pady=6)
    
    def _apply_row_colors(self):
        pass
    
    def _get_installed_databases(self):
        installed = {}
        if not os.path.exists(self.db_path):
            return installed
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, db_category, db_name, version, date, installed, description, path FROM database WHERE installed = 'True' AND db_type != 'host'"
            )
            for row in cursor.fetchall():
                name, db_category, db_name = row[0], row[1], row[2]
                display_name = f"{db_category}/{db_name}" if db_category and db_name else name
                installed[display_name] = {
                    "version": row[3] if row[3] else "N/A",
                    "date": row[4] if row[4] else "N/A",
                    "installed": row[5] if row[5] else "N/A",
                    "description": row[6] if row[6] else "N/A",
                    "path": row[7] if row[7] else "N/A"
                }
            conn.close()
        except sqlite3.OperationalError:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, version, date, installed, description, path FROM database WHERE installed = 'True' AND software != 'host'"
                )
                for row in cursor.fetchall():
                    installed[row[0]] = {
                        "version": row[1] if row[1] else "N/A",
                        "date": row[2] if row[2] else "N/A",
                        "installed": row[3] if row[3] else "N/A",
                        "description": row[4] if row[4] else "N/A",
                        "path": row[5] if row[5] else "N/A"
                    }
                conn.close()
            except Exception as e:
                print(f"Error reading database: {e}")
        except Exception as e:
            print(f"Error reading database: {e}")
        
        return installed

    def _get_all_databases(self):
        installed = {}
        if not os.path.exists(self.db_path):
            return {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM database")
            for row in cursor.fetchall():
                installed[row[0]] = row
            conn.close()
        except Exception as e:
            print(f"Error reading database: {e}")
        
        return installed

    def _get_installed_hosts(self):
        installed = {}
        if not os.path.exists(self.db_path):
            return installed
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, db_category, db_name, path FROM database WHERE installed = 'True' AND db_type = 'host'"
            )
            for row in cursor.fetchall():
                name, db_category, db_name = row[0], row[1], row[2]
                display_name = f"{db_category}/{db_name}" if db_category and db_name else name
                filename = os.path.basename(row[3]) if row[3] else "N/A"
                installed[display_name] = filename
            conn.close()
        except sqlite3.OperationalError:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, path FROM database WHERE installed = 'True' AND software = 'host'"
                )
                for row in cursor.fetchall():
                    filename = os.path.basename(row[1]) if row[1] else "N/A"
                    installed[row[0]] = filename
                conn.close()
            except Exception as e:
                print(f"Error reading database: {e}")
        except Exception as e:
            print(f"Error reading database: {e}")
        
        return installed
    
    def _get_installed_software(self):
        installed = {}
        if not os.path.exists(self.db_path):
            return installed
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, tag FROM software WHERE installed = 'True'")
            for row in cursor.fetchall():
                installed[row[0]] = row[1] if row[1] else "N/A"
            conn.close()
        except Exception as e:
            print(f"Error reading database: {e}")
        
        return installed

    def _get_env_path_from_yaml(self, yaml_file: str) -> str:
        envs_map = ENVS_PARAMS.get("ENVS", {})
        for env_path, yml in envs_map.items():
            if yml == yaml_file:
                return env_path
        return ""

    def _check_conda_binary(self, yaml_file: str, binary_name: str) -> bool:
        env_path = self._get_env_path_from_yaml(yaml_file)
        if not env_path:
            return False
        binary_path = os.path.join(self.env_root, env_path, "bin", binary_name)
        return os.path.isfile(binary_path)

    def _check_archive_installed(self, name: str, soft_info: dict) -> bool:
        install_path = self.ARCHIVE_INSTALL_PATHS.get(name, "")
        if not install_path:
            return False
        full_path = os.path.join(self.env_root, install_path)
        return os.path.exists(full_path)

    def _check_git_installed(self, name: str, soft_info: dict) -> bool:
        install_path = self.GIT_INSTALL_PATHS.get(name, "")
        if not install_path:
            return False
        full_path = os.path.join(self.env_root, install_path)
        return os.path.exists(full_path)

    def export_tsv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".tsv",
            filetypes=[("TSV files", "*.tsv"), ("All files", "*.*")],
            initialfile="televir_status.tsv"
        )
        if not filepath:
            return
        
        with open(filepath, 'w') as f:
            f.write("# TELE-Vir Status Export\n\n")
            
            f.write("# Databases\n")
            f.write("Name\tCategory\tDescription\tAvailable\tInstalled\tVersion\tDate\n")
            for row in self.db_rows_frame.winfo_children():
                labels = row.winfo_children()
                values = [l.cget("text") for l in labels]
                f.write("\t".join(values) + "\n")
            
            f.write("\n# Host Genomes\n")
            f.write("Name\tCommon Name\tAvailable\tInstalled\tFilename\n")
            for row in self.host_rows_frame.winfo_children():
                labels = row.winfo_children()
                values = [l.cget("text") for l in labels]
                f.write("\t".join(values) + "\n")
            
            f.write("\n# Software\n")
            f.write("Name\tType\tAvailable\tInstalled\tTag\n")
            for row in self.soft_rows_frame.winfo_children():
                labels = row.winfo_children()
                values = [l.cget("text") for l in labels]
                f.write("\t".join(values) + "\n")


def main():
    root = TelevirStatusApp()
    root.mainloop()


if __name__ == "__main__":
    main()
