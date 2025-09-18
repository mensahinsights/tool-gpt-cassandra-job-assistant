#!/usr/bin/env python3
"""
Debug script to identify exactly what's going wrong with Google Sheets updates.
Run this locally to see what data is being processed.
"""

import json
from pathlib import Path
import os
from datetime import datetime

def debug_all_result_files():
    """Show all result.json files and their contents."""
    runs_dir = Path("runs")
    if not runs_dir.exists():
        print("❌ No runs directory found")
        return []
    
    result_files = list(runs_dir.glob("*/outputs/result.json"))
    if not result_files:
        print("❌ No result.json files found")
        return []
    
    print(f"📋 Found {len(result_files)} result.json files:")
    print("=" * 80)
    
    file_data = []
    for i, file_path in enumerate(result_files, 1):
        folder_name = file_path.parent.parent.name
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            print(f"\n{i}. FILE: {file_path}")
            print(f"   FOLDER: {folder_name}")
            print(f"   MODIFIED: {file_mtime}")
            print(f"   CONTENT:")
            for key, value in data.items():
                print(f"     {key}: {value}")
            
            file_data.append({
                'path': str(file_path),
                'folder': folder_name,
                'mtime': file_mtime,
                'data': data
            })
            
        except Exception as e:
            print(f"   ❌ ERROR reading file: {e}")
    
    return file_data

def test_latest_detection():
    """Test which file our current logic would pick as 'latest'."""
    print("\n" + "=" * 80)
    print("🔍 TESTING LATEST FILE DETECTION")
    print("=" * 80)
    
    runs_dir = Path("runs")
    result_files = list(runs_dir.glob("*/outputs/result.json"))
    
    if not result_files:
        print("❌ No files to test")
        return
    
    # Test folder name sorting
    print("\n1. BY FOLDER NAME (alphabetical):")
    by_folder = max(result_files, key=lambda f: f.parent.parent.name)
    print(f"   Winner: {by_folder}")
    print(f"   Folder: {by_folder.parent.parent.name}")
    
    # Test modification time
    print("\n2. BY FILE MODIFICATION TIME:")
    by_mtime = max(result_files, key=lambda f: f.stat().st_mtime)
    mtime = datetime.fromtimestamp(by_mtime.stat().st_mtime)
    print(f"   Winner: {by_mtime}")
    print(f"   Modified: {mtime}")
    
    # Test combined approach
    print("\n3. BY FOLDER+TIME (current logic):")
    def sort_key(file_path):
        folder_name = file_path.parent.parent.name
        file_mtime = file_path.stat().st_mtime
        return (folder_name, file_mtime)
    
    by_combined = max(result_files, key=sort_key)
    combined_mtime = datetime.fromtimestamp(by_combined.stat().st_mtime)
    print(f"   Winner: {by_combined}")
    print(f"   Folder: {by_combined.parent.parent.name}")
    print(f"   Modified: {combined_mtime}")

def check_last_result_marker():
    """Check what the .last_result marker contains."""
    print("\n" + "=" * 80)
    print("📌 CHECKING .last_result MARKER")
    print("=" * 80)
    
    marker_path = Path(".last_result")
    if not marker_path.exists():
        print("❌ No .last_result file found")
        return
    
    try:
        with open(marker_path, 'r') as f:
            content = f.read().strip()
        
        print(f"📄 Marker content: {content}")
        
        # Check if the file it points to exists
        if "|" in content:
            file_path, timestamp = content.split("|", 1)
            print(f"📅 Timestamp: {timestamp}")
        else:
            file_path = content
        
        target_file = Path(file_path)
        if target_file.exists():
            print(f"✅ Target file exists: {target_file}")
            try:
                with open(target_file, 'r') as f:
                    data = json.load(f)
                print("📋 Target file contents:")
                for key, value in data.items():
                    print(f"     {key}: {value}")
            except Exception as e:
                print(f"❌ Error reading target file: {e}")
        else:
            print(f"❌ Target file does not exist: {target_file}")
            
    except Exception as e:
        print(f"❌ Error reading marker file: {e}")

def main():
    print("🔧 GOOGLE SHEETS DEBUG TOOL")
    print("=" * 80)
    
    # Show all files
    file_data = debug_all_result_files()
    
    # Test detection logic  
    test_latest_detection()
    
    # Check marker file
    check_last_result_marker()
    
    # Summary
    print("\n" + "=" * 80)
    print("💡 SUMMARY")
    print("=" * 80)
    
    if file_data:
        print(f"Total files found: {len(file_data)}")
        latest_by_folder = max(file_data, key=lambda x: x['folder'])
        latest_by_time = max(file_data, key=lambda x: x['mtime'])
        
        print(f"\nLatest by folder name: {latest_by_folder['folder']}")
        print(f"Latest by file time: {latest_by_time['path']} ({latest_by_time['mtime']})")
        
        if latest_by_folder['folder'] != latest_by_time['folder']:
            print("\n⚠️  MISMATCH: Folder sorting and time sorting give different results!")
            print("This explains why you're getting the wrong data.")

if __name__ == "__main__":
    main()