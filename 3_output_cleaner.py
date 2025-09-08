#!/usr/bin/env python3
"""
Output Cleaner Script

This script processes all JSON files in the outputs directory and creates cleaned versions
in the cleaned_outputs directory. Only files with at least one contact entry in the
contact_info.contacts array are copied to the cleaned_outputs directory.

Usage:
    python 3_output_cleaner.py
"""

import json
import os
import shutil
from pathlib import Path


def process_output_files():
    """
    Process all JSON files in the outputs directory and create cleaned versions
    in cleaned_outputs directory for files that have at least one contact entry.
    """
    # Define directories
    outputs_dir = Path("outputs")
    cleaned_outputs_dir = Path("cleaned_outputs")
    
    # Ensure cleaned_outputs directory exists
    cleaned_outputs_dir.mkdir(exist_ok=True)
    
    # Check if outputs directory exists
    if not outputs_dir.exists():
        print(f"Error: {outputs_dir} directory does not exist!")
        return
    
    # Get all JSON files in outputs directory
    json_files = list(outputs_dir.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {outputs_dir} directory.")
        return
    
    print(f"Found {len(json_files)} JSON files in {outputs_dir} directory.")
    
    processed_count = 0
    copied_count = 0
    
    for json_file in json_files:
        try:
            # Read the JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            processed_count += 1
            
            # Check if the file has the expected structure and at least one contact
            if (isinstance(data, dict) and 
                'contact_info' in data and 
                isinstance(data['contact_info'], dict) and
                'contacts' in data['contact_info'] and
                isinstance(data['contact_info']['contacts'], list) and
                len(data['contact_info']['contacts']) > 0):
                
                # Copy the file to cleaned_outputs directory
                output_file = cleaned_outputs_dir / json_file.name
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                copied_count += 1
                print(f"✓ Copied {json_file.name} (has {len(data['contact_info']['contacts'])} contacts)")
            
            else:
                print(f"✗ Skipped {json_file.name} (no contacts or invalid structure)")
                
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing {json_file.name}: {e}")
        except Exception as e:
            print(f"✗ Error processing {json_file.name}: {e}")
    
    print(f"\nProcessing complete!")
    print(f"Processed: {processed_count} files")
    print(f"Copied to cleaned_outputs: {copied_count} files")
    print(f"Skipped: {processed_count - copied_count} files")


if __name__ == "__main__":
    print("Output Cleaner Script")
    print("=" * 50)
    process_output_files()
