import json
import logging
from datetime import datetime
import os
import customtkinter as ctk
from typing import Dict, Optional
import tkinter as tk
from tkinter import ttk, messagebox

class FileTransferLogger:
    """Handles logging of file transfer activities"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, log_file: str = "EZFileShare.log"):
        if not hasattr(self, 'initialized'):
            self.log_file = log_file
            
            # Configure logging
            logging.basicConfig(
                filename=self.log_file,
                level=logging.INFO,
                format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "event": %(message)s}'
            )
            self.initialized = True
    
    def log_transfer(self, event_type: str, filename: str, host: str, 
                    port: int, status: str, additional_info: Dict = None) -> None:
        """
        Log a file transfer event
        
        Args:
            event_type: Type of event (send/receive)
            filename: Name of the file being transferred
            host: Host address involved in transfer
            port: Port used for transfer
            status: Status of the transfer (success/failed)
            additional_info: Optional dictionary containing additional metadata
        """
        event_data = {
            "type": event_type,
            "filename": filename,
            "host": host,
            "port": port,
            "status": status,
            "additional_info": additional_info or {}
        }
        
        logging.info(json.dumps(event_data))

# Singleton instance for global access
transfer_logger = FileTransferLogger()

class TransferHistoryViewer(ctk.CTkToplevel):
    """Custom tkinter window for viewing transfer history"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Transfer History")
        self.geometry("900x600")
        
        # Create main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Search frame
        self.search_frame = ctk.CTkFrame(self.main_frame)
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create search widgets
        self.create_search_widgets()
        
        # Create table
        self.create_transfer_table()
        
        # Load initial data
        self.load_history()
    
    def create_search_widgets(self):
        """Create search filter widgets"""
        # Date range
        date_frame = ctk.CTkFrame(self.search_frame)
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ctk.CTkLabel(date_frame, text="Date Range:").pack(side=tk.LEFT, padx=5)
        self.date_from = ctk.CTkEntry(date_frame, width=120, placeholder_text="YYYY-MM-DD")
        self.date_from.pack(side=tk.LEFT, padx=5)
        
        ctk.CTkLabel(date_frame, text="to").pack(side=tk.LEFT, padx=5)
        self.date_to = ctk.CTkEntry(date_frame, width=120, placeholder_text="YYYY-MM-DD")
        self.date_to.pack(side=tk.LEFT, padx=5)
        
        # Filters frame
        filters_frame = ctk.CTkFrame(self.search_frame)
        filters_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Event type
        ctk.CTkLabel(filters_frame, text="Event Type:").pack(side=tk.LEFT, padx=5)
        self.event_type = ctk.CTkComboBox(filters_frame, values=["All", "Send", "Receive"])
        self.event_type.pack(side=tk.LEFT, padx=5)
        
        # Host filter
        ctk.CTkLabel(filters_frame, text="Host:").pack(side=tk.LEFT, padx=5)
        self.host_entry = ctk.CTkEntry(filters_frame, width=120)
        self.host_entry.pack(side=tk.LEFT, padx=5)
        
        # Search button
        self.search_btn = ctk.CTkButton(filters_frame, text="Search", command=self.search_history)
        self.search_btn.pack(side=tk.LEFT, padx=20)
    
    def create_transfer_table(self):
        """Create the table for displaying transfer history"""
        # Create frame for treeview
        self.tree_frame = ctk.CTkFrame(self.main_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create treeview with scrollbar
        self.tree = ttk.Treeview(self.tree_frame, style="Custom.Treeview")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ctk.CTkScrollbar(self.tree_frame, command=self.tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        # Configure columns
        self.tree["columns"] = ("timestamp", "type", "filename", "host", "port", "status")
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("timestamp", width=150)
        self.tree.column("type", width=100)
        self.tree.column("filename", width=200)
        self.tree.column("host", width=150)
        self.tree.column("port", width=100)
        self.tree.column("status", width=100)
        
        # Configure headers
        self.tree.heading("#0", text="")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("type", text="Type")
        self.tree.heading("filename", text="Filename")
        self.tree.heading("host", text="Host")
        self.tree.heading("port", text="Port")
        self.tree.heading("status", text="Status")
        
        # Style for dark theme
        style = ttk.Style()
        style.configure("Custom.Treeview",
                       background="#333333",
                       foreground="white",
                       fieldbackground="#333333")
        style.configure("Custom.Treeview.Heading",
                       background="#2b2b2b",
                       foreground="white")
    
    def load_history(self) -> None:
        """Load and display the transfer history"""
        if not os.path.exists("EZFileShare.log"):
            return
            
        try:
            with open("EZFileShare.log", "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        event_data = json.loads(entry["event"])
                        
                        # Insert into treeview
                        self.tree.insert("", tk.END, values=(
                            entry["timestamp"],
                            event_data["type"],
                            event_data["filename"],
                            event_data["host"],
                            event_data["port"],
                            event_data["status"]
                        ))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error loading history: {e}")
    
    def search_history(self) -> None:
        """Filter and display history based on search criteria"""
        # Clear current display
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Get filter values
        date_from = self.date_from.get()
        date_to = self.date_to.get()
        event_type = self.event_type.get()
        host = self.host_entry.get().lower()
        
        try:
            with open("EZFileShare.log", "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        event_data = json.loads(entry["event"])
                        
                        # Apply filters
                        if event_type != "All" and event_data["type"].lower() != event_type.lower():
                            continue
                            
                        if host and event_data["host"].lower() != host:
                            continue
                            
                        # Date filtering
                        if date_from or date_to:
                            entry_date = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S,%f")
                            
                            if date_from:
                                try:
                                    from_date = datetime.strptime(date_from, "%Y-%m-%d")
                                    if entry_date < from_date:
                                        continue
                                except ValueError:
                                    messagebox.showerror("Error", "Invalid 'From' date format. Use YYYY-MM-DD")
                                    return
                            
                            if date_to:
                                try:
                                    to_date = datetime.strptime(date_to, "%Y-%m-%d")
                                    if entry_date > to_date:
                                        continue
                                except ValueError:
                                    messagebox.showerror("Error", "Invalid 'To' date format. Use YYYY-MM-DD")
                                    return
                        
                        # Add matching entry to treeview
                        self.tree.insert("", tk.END, values=(
                            entry["timestamp"],
                            event_data["type"],
                            event_data["filename"],
                            event_data["host"],
                            event_data["port"],
                            event_data["status"]
                        ))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error searching history: {e}")
            