# Coding Assistant Examples

## Generate and Test Code
```
mimo-harness --task "Write a Python function to sort a list using merge sort, then test it with [3,1,4,1,5,9,2,6]"
```

## Debug Code
```
mimo-harness --task "Read the file main.py and find any bugs"
```

## Refactor
```
mimo-harness --task "Refactor the function in utils.py to use list comprehension instead of a for loop"
```

## Add Tests
```
mimo-harness --task "Read calculator.py and write unit tests for all its functions"
```

## Pipe Error Logs
```
cat app.log | mimo-harness -p "Find the root cause of these errors and suggest fixes"
```

## Edit Jupyter Notebook
```
mimo-harness --task "Open analysis.ipynb and add a new cell after cell 5 that plots the distribution"
```

## High-Effort Code Review
```
mimo-harness --effort high --task "Review src/auth.py for security vulnerabilities and suggest fixes"
```

## Bare Mode (Fast)
```
mimo-harness --bare --task "What's the time complexity of quicksort?"
```
