# Office Work Examples

## Create Reports
```
mimo-harness --task "Create a weekly status report markdown file with sections for progress, blockers, and next steps"
```

## Generate Spreadsheets
```
mimo-harness --task "Create a CSV file with a budget table: columns for item, estimated cost, actual cost, and variance"
```

## Summarize Documents
```
mimo-harness --task "Read the file meeting_notes.md and create a summary with action items"
```

## Data Processing
```
mimo-harness --task "Read data.csv, calculate the average of the 'score' column, and create a summary report"
```

## Pipe CSV Data
```
cat sales_q1.csv | mimo-harness -p "Calculate total revenue by region and create a summary table"
```

## JSON Output for Automation
```
mimo-harness --output-format json --task "Analyze report.md and extract all action items"
```

## Resume Previous Session
```
mimo-harness --continue
# Continues where you left off last time
```

## Task Tracking
```
mimo-harness --task "Create tasks for the migration: 1) Update database schema, 2) Migrate data, 3) Update API endpoints, 4) Write tests"
```
