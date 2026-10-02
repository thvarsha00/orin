"""Starter problems for Orin Code.

This file contains plain problem data only.
It does not import anything from the application.

Each test is:

    (input_args, expected_output, is_hidden)

input_args is the list of positional arguments passed to the
problem's entry function.

Problems can specify their language explicitly.
If language is omitted, the seed defaults to Python.
"""


def _fizzbuzz(n: int) -> list[str]:
    return [
        (
            "FizzBuzz"
            if i % 15 == 0
            else "Fizz"
            if i % 3 == 0
            else "Buzz"
            if i % 5 == 0
            else str(i)
        )
        for i in range(1, n + 1)
    ]


TOPICS = [
    "Python Basics",
    "Arrays and Strings",
    "JavaScript Basics",
]


PROBLEMS = [
    {
        "title": "Sum of Even Numbers",
        "topic": "Python Basics",
        "language": "python",
        "difficulty": "easy",
        "description": (
            "Given a list of integers `nums`, return the sum of all "
            "the even numbers in it. If there are no even numbers, "
            "return 0."
        ),
        "examples": [
            {
                "input": "nums = [1, 2, 3, 4]",
                "output": "6",
                "explanation": "2 + 4 = 6",
            }
        ],
        "constraints": (
            "0 <= len(nums) <= 1000. "
            "Each number is between -10^6 and 10^6."
        ),
        "starter_code": (
            "def solve(nums):\n"
            "    # write your code here\n"
            "    pass\n"
        ),
        "expected_complexity": "O(n)",
        "tests": [
            ([[1, 2, 3, 4]], 6, False),
            ([[]], 0, False),
            ([[-2, -4, 5]], -6, False),
            ([[7, 9]], 0, True),
            ([[10**6, 2]], 1000002, True),
        ],
    },

    {
        "title": "Reverse a String",
        "topic": "Python Basics",
        "language": "python",
        "difficulty": "easy",
        "description": "Given a string `s`, return the string reversed.",
        "examples": [
            {
                "input": 's = "hello"',
                "output": '"olleh"',
                "explanation": "",
            }
        ],
        "constraints": "0 <= len(s) <= 1000.",
        "starter_code": (
            "def solve(s):\n"
            "    # write your code here\n"
            "    pass\n"
        ),
        "expected_complexity": "O(n)",
        "tests": [
            (["hello"], "olleh", False),
            ([""], "", False),
            (["a"], "a", False),
            (["racecar"], "racecar", True),
            (["Orin AI"], "IA nirO", True),
        ],
    },

    {
        "title": "Valid Palindrome",
        "topic": "Python Basics",
        "language": "python",
        "difficulty": "easy",
        "description": (
            "Given a string `s`, return `True` if it reads the same "
            "forwards and backwards after ignoring case and everything "
            "that is not a letter or digit, otherwise `False`."
        ),
        "examples": [
            {
                "input": 's = "A man, a plan, a canal: Panama"',
                "output": "True",
                "explanation": (
                    'It becomes "amanaplanacanalpanama", '
                    "which is a palindrome."
                ),
            }
        ],
        "constraints": "0 <= len(s) <= 10^5.",
        "starter_code": (
            "def solve(s):\n"
            "    # write your code here\n"
            "    pass\n"
        ),
        "expected_complexity": "O(n)",
        "tests": [
            (
                ["A man, a plan, a canal: Panama"],
                True,
                False,
            ),
            (["hello"], False, False),
            ([""], True, False),
            (["No lemon, no melon"], True, True),
            (["ab"], False, True),
        ],
    },

    {
        "title": "FizzBuzz List",
        "topic": "Python Basics",
        "language": "python",
        "difficulty": "easy",
        "description": (
            "Given an integer `n`, return a list of strings for the "
            'numbers 1 to n: "FizzBuzz" if divisible by 3 and 5, '
            '"Fizz" if divisible by 3, "Buzz" if divisible by 5, '
            "otherwise the number as a string. For n = 0 return "
            "an empty list."
        ),
        "examples": [
            {
                "input": "n = 5",
                "output": '["1", "2", "Fizz", "4", "Buzz"]',
                "explanation": "",
            }
        ],
        "constraints": "0 <= n <= 10^4.",
        "starter_code": (
            "def solve(n):\n"
            "    # write your code here\n"
            "    pass\n"
        ),
        "expected_complexity": "O(n)",
        "tests": [
            ([5], _fizzbuzz(5), False),
            ([1], ["1"], False),
            ([15], _fizzbuzz(15), False),
            ([0], [], True),
            ([30], _fizzbuzz(30), True),
        ],
    },

    {
        "title": "Two Sum",
        "topic": "Arrays and Strings",
        "language": "python",
        "difficulty": "medium",
        "description": (
            "Given a list of integers `nums` and an integer `target`, "
            "return the indices `[i, j]` (with i < j) of the two "
            "numbers that add up to `target`. Exactly one such pair "
            "exists, and you may not use the same element twice."
        ),
        "examples": [
            {
                "input": "nums = [2, 7, 11, 15], target = 9",
                "output": "[0, 1]",
                "explanation": (
                    "nums[0] + nums[1] = 2 + 7 = 9"
                ),
            }
        ],
        "constraints": (
            "2 <= len(nums) <= 10^4. "
            "Aim for better than O(n^2)."
        ),
        "starter_code": (
            "def solve(nums, target):\n"
            "    # write your code here\n"
            "    pass\n"
        ),
        "expected_complexity": "O(n)",
        "tests": [
            ([[2, 7, 11, 15], 9], [0, 1], False),
            ([[3, 2, 4], 6], [1, 2], False),
            ([[3, 3], 6], [0, 1], False),
            (
                [[-1, -2, -3, -4, -5], -8],
                [2, 4],
                True,
            ),
            ([[1, 5, 6, 9], 14], [1, 3], True),
            ([[0, 4, 3, 0], 0], [0, 3], True),
        ],
    },

    {
        "title": "Sum of Array",
        "topic": "JavaScript Basics",
        "language": "javascript",
        "difficulty": "easy",
        "description": (
            "Given an array of numbers, return the sum of all "
            "elements in the array."
        ),
        "examples": [
            {
                "input": "nums = [1, 2, 3, 4]",
                "output": "10",
                "explanation": "1 + 2 + 3 + 4 = 10",
            }
        ],
        "constraints": (
            "0 <= len(nums) <= 1000. "
            "Each number is between -10^6 and 10^6."
        ),
        "starter_code": (
            "function solve(nums) {\n"
            "    // write your code here\n"
            "}\n"
        ),
        "expected_complexity": "O(n)",
        "tests": [
            ([[1, 2, 3, 4]], 10, False),
            ([[]], 0, False),
            ([[-2, 5, 7]], 10, False),
            ([[100, 200, 300]], 600, True),
            ([[-10, -20, -30]], -60, True),
        ],
    },
]