#!/usr/bin/env python3
"""
Debug script to identify patterns that might not show visualization markers.
This script analyzes pattern data and checks visualization coverage.
"""

import requests
import json
import sys
from typing import Dict, List, Any

def analyze_pattern_visualization():
    """Test pattern visualization coverage and identify potential issues"""
    
    base_url = "http://127.0.0.1:8000"
    
    # Test different endpoints
    test_cases = [
        ("bitcoin", "1d", 7),
        ("bitcoin", "4h", 3), 
        ("bitcoin", "1h", 1)
    ]
    
    print("Pattern Visualization Debug Analysis")
    print("=" * 50)
    
    all_issues = []
    
    for coin, timeframe, days in test_cases:
        print(f"\nTesting {coin} - {timeframe} timeframe ({days} days)")
        print("-" * 40)
        
        try:
            url = f"{base_url}/patterns/{coin}?days={days}&timeframe={timeframe}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"API Error: {response.status_code}")
                continue
                
            data = response.json()
            patterns = data.get("patterns", [])
            market_data = data.get("market_data", [])
            
            print(f"Found {len(patterns)} patterns, {len(market_data)} market data points")
            
            # Analyze each pattern
            patterns_with_issues = []
            patterns_without_coords = []
            patterns_with_invalid_coords = []
            patterns_with_good_coords = []
            
            for i, pattern in enumerate(patterns):
                pattern_name = pattern.get("name", f"Pattern_{i}")
                coordinates = pattern.get("coordinates")
                
                if not coordinates:
                    patterns_without_coords.append(pattern_name)
                    print(f"⚠️  {pattern_name}: No coordinates")
                else:
                    coord_type = coordinates.get("type", "unknown")
                    print(f"✅ {pattern_name}: {coord_type} coordinates")
                    
                    # Check if coordinates have required fields for visualization
                    if coord_type == "pattern_range":
                        required_fields = ["start_time", "end_time", "pattern_high", "pattern_low"]
                        missing_fields = [f for f in required_fields if f not in coordinates]
                        if missing_fields:
                            patterns_with_invalid_coords.append((pattern_name, f"missing: {missing_fields}"))
                        else:
                            patterns_with_good_coords.append(pattern_name)
                            
                    elif coord_type == "volume_pattern":
                        required_fields = ["timestamp", "volume"]
                        missing_fields = [f for f in required_fields if f not in coordinates]
                        if missing_fields:
                            patterns_with_invalid_coords.append((pattern_name, f"missing: {missing_fields}"))
                        else:
                            patterns_with_good_coords.append(pattern_name)
                            
                    elif coord_type == "statistical_pattern":
                        required_fields = ["timestamp", "price"]
                        missing_fields = [f for f in required_fields if f not in coordinates]
                        if missing_fields:
                            patterns_with_invalid_coords.append((pattern_name, f"missing: {missing_fields}"))
                        else:
                            patterns_with_good_coords.append(pattern_name)
                            
                    elif coord_type == "horizontal_line":
                        required_fields = ["level", "start_time", "end_time"]
                        missing_fields = [f for f in required_fields if f not in coordinates]
                        if missing_fields:
                            patterns_with_invalid_coords.append((pattern_name, f"missing: {missing_fields}"))
                        else:
                            patterns_with_good_coords.append(pattern_name)
                            
                    elif coord_type == "harmonic_pattern":
                        if "points" not in coordinates or len(coordinates.get("points", [])) < 2:
                            patterns_with_invalid_coords.append((pattern_name, "insufficient harmonic points"))
                        else:
                            patterns_with_good_coords.append(pattern_name)
                    else:
                        patterns_with_invalid_coords.append((pattern_name, f"unknown coordinate type: {coord_type}"))
            
            # Summary for this test case
            print(f"\n📋 Summary for {coin} {timeframe}:")
            print(f"   ✅ Patterns with good coordinates: {len(patterns_with_good_coords)}")
            print(f"   ⚠️  Patterns without coordinates: {len(patterns_without_coords)}")
            print(f"   ❌ Patterns with invalid coordinates: {len(patterns_with_invalid_coords)}")
            
            if patterns_without_coords:
                print(f"   📝 Without coordinates: {', '.join(patterns_without_coords)}")
                all_issues.extend([(coin, timeframe, p, "no_coordinates") for p in patterns_without_coords])
                
            if patterns_with_invalid_coords:
                print(f"   📝 Invalid coordinates:")
                for pattern_name, issue in patterns_with_invalid_coords:
                    print(f"      - {pattern_name}: {issue}")
                    all_issues.append((coin, timeframe, pattern_name, f"invalid_coords: {issue}"))
            
            # Test pattern fallback capability
            if patterns_without_coords or patterns_with_invalid_coords:
                print(f"\n🔧 Fallback Visualization Test:")
                print(f"   - Market data available: {len(market_data)} points")
                if len(market_data) >= 5:
                    print(f"   ✅ Sufficient market data for fallback visualization")
                else:
                    print(f"   ❌ Insufficient market data for fallback ({len(market_data)} < 5)")
                    
        except Exception as e:
            print(f"❌ Error testing {coin} {timeframe}: {e}")
            all_issues.append((coin, timeframe, "API_ERROR", str(e)))
    
    # Final summary
    print("\n" + "=" * 50)
    print("🏁 FINAL ANALYSIS SUMMARY")
    print("=" * 50)
    
    if not all_issues:
        print("✅ All patterns have proper visualization coordinates!")
        print("   No patterns should be missing markers when selected.")
    else:
        print(f"❌ Found {len(all_issues)} potential visualization issues:")
        for coin, timeframe, pattern, issue in all_issues:
            print(f"   - {coin} {timeframe}: {pattern} - {issue}")
        
        print(f"\n💡 Recommendations:")
        print(f"   1. Patterns without coordinates rely on fallback visualization")
        print(f"   2. Check if fallback visualization is working in frontend")
        print(f"   3. Consider removing patterns that cannot be visualized")
    
    # Check if there are patterns that should be filtered out
    unreliable_patterns = []
    for coin, timeframe, pattern, issue in all_issues:
        if "no_coordinates" in issue and pattern not in ["Support Level Test", "Resistance Level Test"]:
            unreliable_patterns.append(pattern)
    
    if unreliable_patterns:
        print(f"\n🚫 Patterns that should potentially be filtered from UI:")
        for pattern in set(unreliable_patterns):
            print(f"   - {pattern}")
    
    return all_issues

if __name__ == "__main__":
    try:
        issues = analyze_pattern_visualization()
        if issues:
            sys.exit(1)  # Exit with error if issues found
        else:
            sys.exit(0)  # Success
    except KeyboardInterrupt:
        print("\n🛑 Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)