#!/usr/bin/env python
"""
WTG Visualization Script for APV
This script runs Gator analysis with visualization output and opens the results in a browser
"""

import os
import sys
import subprocess
import webbrowser
import time

def main():
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 70)
    print("WTG Visualization Tool for APV")
    print("=" * 70)
    print()
    
    # Run Gator with visualization client
    print("[1/3] Running Gator analysis with WTG visualization...")
    cmd = ["python", "runGator.py", "-j", "apv/config.json", "-p", "apv"]
    
    try:
        result = subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:", result.stderr)
        
        if result.returncode != 0:
            print("Error running Gator. Return code:", result.returncode)
            return
    except Exception as e:
        print(f"Error running Gator: {e}")
        return
    
    print()
    print("[2/3] Looking for generated files...")
    
    # Find the generated HTML file in output directory
    html_file = None
    dot_file = None
    
    # Check in output/apv/results directory
    output_dir = os.path.join(script_dir, "..", "output", "apv", "results")
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            if f.endswith("_wtg_viewer.html"):
                html_file = os.path.join(output_dir, f)
            if f.endswith("_wtg.dot"):
                dot_file = os.path.join(output_dir, f)
    
    if html_file and os.path.exists(html_file):
        print(f"✓ Found HTML viewer: {html_file}")
    else:
        print("✗ HTML viewer not found")
    
    if dot_file and os.path.exists(dot_file):
        print(f"✓ Found DOT file: {dot_file}")
    else:
        print("✗ DOT file not found")
    
    print()
    print("[3/3] Opening visualization...")
    
    if html_file and os.path.exists(html_file):
        # Open in default browser
        file_url = f"file:///{html_file.replace(os.sep, '/')}"
        print(f"Opening: {file_url}")
        webbrowser.open(file_url)
        
        print()
        print("=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print("The WTG visualization should now be open in your browser.")
        print()
        print("Files generated:")
        print(f"  - HTML Viewer: {html_file}")
        if dot_file:
            print(f"  - DOT File: {dot_file}")
        print()
        print("Source code location:")
        source_dir = os.path.join(script_dir, "..", "output", "apv", "source")
        if os.path.exists(source_dir):
            print(f"  - Decoded APK: {source_dir}")
        print()
        print("To visualize the graph:")
        print("  1. Use the HTML viewer (already opened)")
        print("  2. Copy DOT content from the 'DOT File' tab")
        print("  3. Paste at: https://dreampuf.github.io/GraphvizOnline/")
        print()
    else:
        print("=" * 70)
        print("ERROR: Could not find generated visualization files")
        print("=" * 70)
        print("Please check the Gator output above for errors.")
        print("The visualization client may not have been invoked correctly.")

if __name__ == "__main__":
    main()
