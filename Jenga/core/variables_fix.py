def expand_path_patterns(pattern: str, base_dir: str = ".") -> list:
    """
    Expand path patterns with wildcards
    """
    from pathlib import Path
    
    results = []
    exclude = False
    
    # Check for exclusion prefix
    if pattern.startswith("!"):
        exclude = True
        pattern = pattern[1:].strip()
    
    # Convert to Path and handle absolute vs relative
    pattern_path = Path(pattern)
    
    if pattern_path.is_absolute():
        # Absolute path: use it directly
        working_pattern = pattern
        base_path = Path("/")
    else:
        # Relative path: use base_dir
        base_path = Path(base_dir)
        working_pattern = pattern
    
    # Handle ** recursive patterns
    if "**" in working_pattern:
        # Split on **
        parts = working_pattern.split("**", 1)
        prefix = parts[0].rstrip("/\\")
        suffix = parts[1].lstrip("/\\") if len(parts) > 1 else ""
        
        # Determine search directory
        if prefix:
            if Path(prefix).is_absolute():
                search_dir = Path(prefix)
            else:
                search_dir = base_path / prefix
        else:
            search_dir = base_path
        
        # Search recursively
        if search_dir.exists() and search_dir.is_dir():
            # If suffix has *, use it as pattern, otherwise match exact names
            if suffix:
                for file_path in search_dir.rglob(suffix):
                    if file_path.is_file():
                        results.append((str(file_path), exclude))
            else:
                # No suffix, match all files
                for file_path in search_dir.rglob("*"):
                    if file_path.is_file():
                        results.append((str(file_path), exclude))
    
    # Handle * non-recursive patterns
    elif "*" in working_pattern:
        if Path(working_pattern).is_absolute():
            # Absolute pattern
            parent = Path(working_pattern).parent
            pattern_name = Path(working_pattern).name
            if parent.exists():
                for file_path in parent.glob(pattern_name):
                    if file_path.is_file():
                        results.append((str(file_path), exclude))
        else:
            # Relative pattern
            parts = working_pattern.rsplit("/", 1)
            if len(parts) == 2:
                search_dir = base_path / parts[0]
                file_pattern = parts[1]
            else:
                search_dir = base_path
                file_pattern = working_pattern
            
            if search_dir.exists():
                for file_path in search_dir.glob(file_pattern):
                    if file_path.is_file():
                        results.append((str(file_path), exclude))
    
    # Handle exact file paths
    else:
        if Path(working_pattern).is_absolute():
            file_path = Path(working_pattern)
        else:
            file_path = base_path / working_pattern
        
        if file_path.exists() and file_path.is_file():
            results.append((str(file_path), exclude))
    
    return results
