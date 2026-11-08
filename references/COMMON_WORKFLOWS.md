# Common Workflows

Ordered procedures for frequent Recruit tasks. Every workflow starts with live tool discovery, because the MCP tool names come from the server, not from this repository.

Workflows here describe the documented Recruit capabilities. The actual call goes through whichever live tool exposes that capability.

## Preparation (once per session)

```bash
python3 scripts/discover_tools.py --json --save /tmp/recruit-tools.json
```

Confirm the tools for the current account before any data access. Do not reuse a tool list from another account.

## Triage a new applicant

Goal: find and summarize recent applicants for an open role.

1. Discover the tools and identify the record-read and search tools.
2. Read the open job openings for the role. Use the record-read tool with the job opening module and the job opening ID.
3. Search candidates in that job opening using the search tool and its criteria filter.
4. For each candidate, read the record before summarizing. Never infer stage, source, or status from a search result alone.
5. Report using IDs, not names, where a later write may follow. Never copy contact details into the summary unless asked.

Check: the job opening ID, the candidate IDs, and each candidate's stage are all confirmed from a live read.

## Move a candidate to the next stage

Goal: advance one candidate in the hiring pipeline.

1. Read the candidate record. Note the current stage, the job opening, and the source.
2. Confirm with the user which candidate and which target stage. A stage change is visible to the hiring team and to the applicant.
3. Change the status or stage using the live status-change tool.
4. Read the candidate back and confirm the stage actually changed.

Check: the stage read back matches the intended target, and the candidate ID and job opening ID are unchanged.

Risk: pipeline-level stage changes affect every candidate in that stage. Never change a shared stage definition to move one candidate.

## Write a recruiter note

Goal: record context about an applicant.

1. Read the candidate record first, so the note refers to the correct person.
2. Compose the note. Include only what is needed for recruiting decisions.
3. Create the note with the live note tool, referencing the correct candidate ID.
4. Read the note back.

Check: the note is attached to the intended candidate and contains no unrelated personal data.

Risk: notes can be visible to other recruiters and, depending on configuration, to clients. Do not paste assessment results or sensitive personal data into a note without an explicit instruction.

## Add and remove tags

Goal: label candidates for a sourcing campaign.

1. Read the candidate record.
2. Use the live add-tags tool with the candidate ID and tag name.
3. Confirm with the live tag-list tool that the tag exists before adding it.
4. Read the candidate back and confirm the tag is attached.

Check: the tag is present on the candidate and no unrelated tag was added or removed.

Risk: `Merge Tags` and `Delete Tags` affect every record carrying the tag. Keep them out of routine profiles.

## List attachments on a candidate

Goal: check whether a CV or other document is on file.

1. Read the candidate record.
2. List attachments with the live attachment-listing tool.
3. Download only what the task needs.

Check: the attachment belongs to the intended candidate.

Risk: attachments are applicant personal data. Do not write them to logs, tickets, chats, or a repository. Verify any binary transfer by reading it back.

## Report on pipeline volume

Goal: count or summarize applicants per job opening.

1. Read job openings.
2. Read applications per job opening, paging through results.
3. Aggregate counts and stage distribution.
4. Report counts and job opening IDs. Do not include candidate names or contact details in a volume report unless asked.

Check: every count traces back to a live read, and page boundaries were handled.

Risk: bulk read exports entire modules as files. Use it only for an explicit authorized task, and treat the export as applicant personal data.

## Prepare an interview

Goal: check interview scheduling state.

1. Read the candidate record and the related interviews using the live related-records tool.
2. Read each interview's details before reporting.
3. Scheduling and cancellation are side effects. Confirm before cancelling or rescheduling.

Check: interview IDs, candidate IDs, and the scheduled time all come from a live read.

Risk: cancelling an interview sends a notification to the candidate and the interviewer. Treat it as external communication requiring the active approval policy.

## Verify a record before writing

Use this as the mandatory pre-write check:

1. Read the record by ID.
2. Confirm the ID, the job opening, and the current stage or status.
3. Search for duplicates when creating: same email and same name across the module.
4. Send only the intended fields.
5. Read the record back and diff against what was intended.

Check: the read-back matches the intent on every field you changed, and no other field moved.
