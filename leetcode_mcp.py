import requests
import json
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
from datetime import datetime
import os
from openai import OpenAI
from config import load_api_key
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Solution:
    approach_name: str
    intuition: str
    time_complexity: str
    space_complexity: str
    code: str
    explanation: str

@dataclass
class LeetCodeProblem:
    title: str
    difficulty: str
    description: str
    examples: List[Dict[str, str]]
    constraints: List[str]
    solutions: List[Solution]

class LeetCodeMCP:
    def __init__(self):
        self.graphql_url = "https://leetcode.com/graphql"
        self.session = requests.Session()
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://leetcode.com/problems/"
        }
        # Initialize OpenAI client with API key from config
        api_key = load_api_key()
        self.client = OpenAI(api_key=api_key)
    
    def _sanitize_problem_name(self, name: str) -> str:
        """Convert problem name to leetcode URL format."""
        return name.lower().replace(" ", "-")
    
    def generate_solution(self, problem: LeetCodeProblem) -> Optional[Solution]:
        """
        Generate a solution using OpenAI's API with rate limit handling.
        """
        try:
            # Construct the prompt
            prompt = f"""Given this LeetCode problem:

Title: {problem.title}
Difficulty: {problem.difficulty}

Description:
{problem.description}

Examples:
{chr(10).join(f"Example {i+1}:" + chr(10) + f"Input: {ex.get('input', 'N/A')}" + chr(10) + f"Output: {ex.get('output', 'N/A')}" + (chr(10) + f"Explanation: {ex['explanation']}" if 'explanation' in ex else '') for i, ex in enumerate(problem.examples))}

Constraints:
{chr(10).join('- ' + c for c in problem.constraints)}"""

            try:
                # Get completion from OpenAI
                completion = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Changed from gpt-4o to gpt-3.5-turbo
                    messages=[
                        {"role": "system", "content": "You are an expert programmer helping to solve LeetCode problems. Provide clear, efficient solutions with detailed explanations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )

                # Parse the response
                response_text = completion.choices[0].message.content
                print("\nParsing AI response...")
                solution_data = json.loads(response_text)

                return Solution(
                    approach_name="AI Generated Solution",
                    intuition=solution_data["intuition"],
                    time_complexity=solution_data["time_complexity"],
                    space_complexity=solution_data["space_complexity"],
                    code=solution_data["code"],
                    explanation=solution_data["explanation"]
                )

            except Exception as e:
                error_msg = str(e)
                if "insufficient_quota" in error_msg:
                    print("\nError: OpenAI API quota exceeded. Please check your billing details at https://platform.openai.com/account/billing")
                    print("You can:")
                    print("1. Add funds to your OpenAI account")
                    print("2. Wait for your quota to reset")
                    print("3. Use a different API key")
                    
                    # Return a basic template solution instead
                    return Solution(
                        approach_name="Template Solution",
                        intuition="Please implement your solution here",
                        time_complexity="Analyze the time complexity of your solution",
                        space_complexity="Analyze the space complexity of your solution",
                        code=next(
                            (s["code"] for s in problem.codeSnippets 
                             if s["langSlug"] == "python3"), 
                            "def solution():\n    # Implement your solution here\n    pass"
                        ),
                        explanation="Add a detailed explanation of your approach"
                    )
                elif "429" in error_msg:
                    print("\nError: Rate limit reached. Please try again in a few minutes.")
                else:
                    print(f"\nError generating solution: {error_msg}")
                return None

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None

    def get_problem(self, problem_name: str) -> Optional[LeetCodeProblem]:
        """
        Fetch problem details using LeetCode's GraphQL API.
        """
        try:
            # GraphQL query to get problem details
            query = """
            query getQuestionDetail($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    questionId
                    title
                    difficulty
                    content
                    exampleTestcases
                    topicTags {
                        name
                    }
                    codeSnippets {
                        langSlug
                        code
                    }
                }
            }
            """
            
            variables = {
                "titleSlug": self._sanitize_problem_name(problem_name)
            }
            
            response = self.session.post(
                self.graphql_url,
                headers=self.headers,
                json={
                    "query": query,
                    "variables": variables
                }
            )
            
            # Print response status and headers for debugging
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {response.headers}")
            
            response.raise_for_status()
            
            data = response.json()
            if "errors" in data:
                logger.error(f"GraphQL Error: {data['errors']}")
                return None
                
            question_data = data["data"]["question"]
            if not question_data:
                logger.error(f"Problem '{problem_name}' not found")
                return None
            
            # Parse examples from the content
            examples = []
            content = question_data["content"]
            example_sections = content.split("Example")[1:]
            for i, section in enumerate(example_sections, 1):
                example = {}
                lines = section.strip().split("\n")
                for line in lines:
                    if "Input:" in line:
                        example["input"] = line.split("Input:")[1].strip()
                    elif "Output:" in line:
                        example["output"] = line.split("Output:")[1].strip()
                    elif "Explanation:" in line:
                        example["explanation"] = line.split("Explanation:")[1].strip()
                if example:
                    examples.append(example)
            
            # Extract constraints
            constraints = []
            if "Constraints:" in content:
                constraints_section = content.split("Constraints:")[1].split("\n")
                for line in constraints_section:
                    if line.strip().startswith("*"):
                        constraints.append(line.strip("* "))
            
            # Create default solutions list
            solutions = []
            
            # Generate AI solution
            ai_solution = self.generate_solution(LeetCodeProblem(
                title=question_data["title"],
                difficulty=question_data["difficulty"],
                description=question_data["content"],
                examples=examples,
                constraints=constraints,
                solutions=[]
            ))

            
            if ai_solution:
                solutions.append(ai_solution)
            
            return LeetCodeProblem(
                title=question_data["title"],
                difficulty=question_data["difficulty"],
                description=question_data["content"],
                examples=examples,
                constraints=constraints,
                solutions=solutions
            )
            
        except requests.RequestException as e:
            logger.error(f"Network error: {e}")
            print(f"Full error details: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing problem: {e}")
            print(f"Full error details: {str(e)}")
            return None

    def explain_solutions(self, problem: LeetCodeProblem) -> str:
        """Generate a detailed explanation of all solutions for a problem."""
        explanation = f"# {problem.title}\n\n"
        explanation += f"Difficulty: {problem.difficulty}\n\n"
        explanation += "## Problem Description\n\n"
        explanation += f"{problem.description}\n\n"
        
        explanation += "## Examples\n\n"
        for i, example in enumerate(problem.examples, 1):
            explanation += f"### Example {i}\n"
            explanation += f"Input: {example.get('input', 'N/A')}\n"
            explanation += f"Output: {example.get('output', 'N/A')}\n"
            if 'explanation' in example:
                explanation += f"Explanation: {example['explanation']}\n"
            explanation += "\n"
        
        explanation += "## Constraints\n\n"
        for constraint in problem.constraints:
            explanation += f"- {constraint}\n"
        explanation += "\n"
        
        explanation += "## Solutions\n\n"
        for i, solution in enumerate(problem.solutions, 1):
            explanation += f"### Solution {i}: {solution.approach_name}\n\n"
            explanation += "#### Intuition\n"
            explanation += f"{solution.intuition}\n\n"
            explanation += "#### Complexity Analysis\n"
            explanation += f"- Time Complexity: {solution.time_complexity}\n"
            explanation += f"- Space Complexity: {solution.space_complexity}\n\n"
            explanation += "#### Implementation\n"
            explanation += f"```python\n{solution.code}\n```\n\n"
            explanation += "#### Detailed Explanation\n"
            explanation += f"{solution.explanation}\n\n"
        
        return explanation

def main():
    mcp = LeetCodeMCP()
    
    while True:
        print("\nLeetCode Problem Explorer")
        print("1. Search for a problem")
        print("2. Exit")
        
        choice = input("\nEnter your choice (1-2): ")
        
        if choice == "2":
            break
        elif choice == "1":
            problem_name = input("\nEnter LeetCode problem name (e.g., 'two-sum' or 'valid sudoku'): ")
            print("\nFetching problem details...")
            
            problem = mcp.get_problem(problem_name)
            
            if problem:
                explanation = mcp.explain_solutions(problem)
                print("\n" + explanation)
                
                # Option to save to file
                save = input("\nWould you like to save this explanation to a file? (y/n): ")
                if save.lower() == 'y':
                    filename = f"{problem_name}_explanation.md"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(explanation)
                    print(f"\nExplanation saved to {filename}")
            else:
                print("\nFailed to fetch problem details. Please check the problem name and try again.")
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main() 