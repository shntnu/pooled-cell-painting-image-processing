#!/bin/bash

# Simple script to check if files in a list exist
# Usage: ./check_files.sh file_list.txt [base_directory]

file_list="$1"
base_dir="${2:-}"

if [ ! -f "$file_list" ]; then
  echo "Error: File list $file_list does not exist"
  exit 1
fi

missing=0
total=0

while read -r file; do
  # Skip empty lines
  if [ -z "$file" ]; then continue; fi
  
  ((total++))
  
  # Use base directory if provided
  if [ -n "$base_dir" ]; then
    path="$base_dir/$file"
  else
    path="$file"
  fi
  
  if [ ! -e "$path" ]; then
    echo "Missing: $file"
    ((missing++))
  fi
done < "$file_list"

echo "Checked $total files. Found: $((total-missing)), Missing: $missing" 