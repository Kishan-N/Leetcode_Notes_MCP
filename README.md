# LeetCode MCP (Model Context Protocol)

This is a Python-based tool that fetches LeetCode problems and provides detailed explanations of various solution approaches.

## Features

- Fetches problem descriptions from LeetCode
- Extracts examples and constraints
- Provides multiple solution approaches with:
  - Intuition behind the solution
  - Time and space complexity analysis
  - Implementation details
  - Step-by-step explanations

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python leetcode_mcp.py
```

When prompted, enter the name of the LeetCode problem you want to explore. The tool will fetch the problem and provide detailed explanations of various solution approaches.

Example:
```bash
Enter LeetCode problem name: valid-sudoku
```

## Output Format

The tool generates a markdown-formatted output with:

1. Problem title and difficulty
2. Problem description
3. Examples
4. Constraints
5. Multiple solution approaches, each containing:
   - Intuition
   - Complexity analysis
   - Implementation
   - Detailed explanation

## Note

This tool scrapes data from LeetCode's public problem pages. Please be mindful of LeetCode's terms of service and rate limiting when using this tool. 
