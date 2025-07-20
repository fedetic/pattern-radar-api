#!/usr/bin/env python3
"""
Debug script to identify patterns that might not show visualization markers.
"""

import requests
import json

def analyze_patterns():
    """Analyze pattern visualization coverage"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("Pattern Visualization Analysis")
    print("=" * 40)
    
    try:
        url = f"{base_url}/patterns/bitcoin?days=7&timeframe=1d"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return []
            
        data = response.json()
        patterns = data.get("patterns", [])
        market_data = data.get("market_data", [])
        
        print(f"Found {len(patterns)} patterns, {len(market_data)} market data points")
        print()
        
        issues = []
        
        for i, pattern in enumerate(patterns):
            name = pattern.get("name", f"Pattern_{i}")
            category = pattern.get("category", "Unknown")
            confidence = pattern.get("confidence", 0)
            direction = pattern.get("direction", "unknown")
            coords = pattern.get("coordinates")
            
            print(f"Pattern {i+1}: {name}")
            print(f"  Category: {category}")
            print(f"  Direction: {direction}")
            print(f"  Confidence: {confidence}%")
            
            if not coords:
                print("  Coordinates: MISSING - will use fallback")
                issues.append((name, "no_coordinates"))
            else:
                coord_type = coords.get("type", "unknown")
                print(f"  Coordinates: {coord_type}")
                
                # Check specific coordinate requirements
                if coord_type == "pattern_range":
                    required = ["start_time", "end_time", "pattern_high", "pattern_low"]
                    missing = [f for f in required if f not in coords]
                    if missing:
                        print(f"    ISSUE: Missing fields: {missing}")
                        issues.append((name, f"missing_fields: {missing}"))
                    else:
                        print("    OK: All required fields present")
                        
                elif coord_type == "volume_pattern":
                    required = ["timestamp", "volume"]
                    missing = [f for f in required if f not in coords]
                    if missing:
                        print(f"    ISSUE: Missing fields: {missing}")
                        issues.append((name, f"missing_fields: {missing}"))
                    else:
                        print("    OK: All required fields present")
                        
                elif coord_type == "statistical_pattern":
                    required = ["timestamp", "price"]
                    missing = [f for f in required if f not in coords]
                    if missing:
                        print(f"    ISSUE: Missing fields: {missing}")
                        issues.append((name, f"missing_fields: {missing}"))
                    else:
                        print("    OK: All required fields present")
                        
                elif coord_type == "horizontal_line":
                    required = ["level", "start_time", "end_time"]
                    missing = [f for f in required if f not in coords]
                    if missing:
                        print(f"    ISSUE: Missing fields: {missing}")
                        issues.append((name, f"missing_fields: {missing}"))
                    else:
                        print("    OK: All required fields present")
                        
                elif coord_type == "harmonic_pattern":
                    points = coords.get("points", [])
                    if len(points) < 2:
                        print(f"    ISSUE: Insufficient harmonic points: {len(points)}")
                        issues.append((name, f"insufficient_points: {len(points)}"))
                    else:
                        print(f"    OK: {len(points)} harmonic points")
                else:
                    print(f"    UNKNOWN: Coordinate type '{coord_type}'")
                    issues.append((name, f"unknown_coord_type: {coord_type}"))
            
            print()
        
        print("=" * 40)
        print("SUMMARY:")
        if not issues:
            print("All patterns have proper visualization data!")
        else:
            print(f"Found {len(issues)} potential issues:")
            for name, issue in issues:
                print(f"  - {name}: {issue}")
        
        return issues
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    analyze_patterns()