# NBA Over/Under Daily Tracker

The NBA Over/Under Daily Tracker is a Python application designed to swiftly gather data for every game scheduled on a given day. With this tool, you can access current information on each quarter, team totals, and the current over/under for each NBA game.

To ensure accurate and up-to-date data, the NBA Over/Under Daily Tracker pulls information from both the NBA official API and Odds-API. It's worth noting that Odds-API offers up to 500 free monthly calls for your convenience.

*In order to make sure that you do not go over the montly quota for usage of Odd-API, you can set the threading on refresh_over_under_periodically to refresh at a slower rate*

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Contributing](#contributing)
- [Bugs and Issues](#bugs-and-issues)

## Installation

1. Clone the repository:

    ```
    git clone https://github.com/ehoffman66/nba-over-under-tracker.git
    ```

2. Navigate to the project directory:

    ```
    cd nba-over-under-tracker
    ```

3. Sign up at the-odds-api.com for a free API key 


4. Create a config.ini:

    ```
    [API_Key]
    key = YOURAPIKEY
    ```

5. Run the project:

    ```
    python3 nba-live-data.py
    ```
    
Note: This project requires Python 3.6 or later.

## Examples

...

## Contributing

Thank you for considering contributing to our project! We welcome contributions from anyone, and appreciate your help in making our project better.

## Ways to Contribute

There are several ways you can contribute to our project:

- Report bugs and suggest new features by opening issues on our issue tracker.
- Submit code changes or documentation updates by creating pull requests on GitHub.

## Guidelines

To ensure that your contributions are as helpful as possible, please follow these guidelines:

- Before opening a new issue, please search the issue tracker to see if a similar issue has already been reported.
- Before submitting a pull request, please make sure that your code follows our coding style guidelines, and that all tests pass.
- When submitting documentation updates, please make sure that your changes are clear and concise, and that they follow our documentation standards.


## Bugs and Issues

...
