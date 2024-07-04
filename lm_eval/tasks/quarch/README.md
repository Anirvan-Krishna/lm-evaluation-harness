# Task Name: QuArch

## How to Run:
- Open Terminal at the file location
- The desired file should be having a format similar to QuArch_v0_1_1 and the name should be *data.json*
- Enter the command as follows to work with OpenAI API based models:
```
!OPENAI_API_KEY= [YOUR API KEY] lm_eval --model openai-chat-completions \
  --model_args model=gpt-4o \
  --tasks quarch \
  --limit 50 \
  --output quarch/ \
  --log_samples
```

## File Outputs and Scrutiny
- This command returns the F1-Score on the dataset and saves the samples and result in a folder called *quarch* in the current working directory
- The *quarch* folder contains a file called samples_quarch that contains comprehensive details of the original data, data labels and predicted labels
- To review the mistakes done in prediction by the model, the given code can be run:
```
import json

with open([PATH TO THE SAMPLE FILE], 'r') as file:
    data = json.load(file)

correct_count = 0
total_count = 0
no_targets_count = 0

mismatched_entries = []

for doc in data:
    target = doc['target'].strip().lower()
    resp = doc['filtered_resps'][0].strip().lower()

    if target == "no":
        no_targets_count += 1

    if target == resp:
        correct_count += 1
    else:
        mismatched_entries.append(doc)
    total_count += 1

if total_count > 0:
    correctness_percentage = (correct_count / total_count) * 100
else:
    correctness_percentage = 0

print(f'Correctness Percentage: {correctness_percentage:.2f}%')
print(f'Number of targets which are "NO": {no_targets_count}')

print('\nMismatched Entries:')
for entry in mismatched_entries:
    print(f'Doc ID: {entry["doc_id"]}')
    print(f'Target: {entry["target"]}')
    print(f'Response: {entry["filtered_resps"][0]}')
    print('-' * 50)
```
- If you want to run the task with different models, remember to remove the folder *quarch* from your current working directory

## Working Team:
Anirvan Krishna, Ujjwal Kumar, Nandini Bhattad, Aarya Pakhale, Rushi Chavda