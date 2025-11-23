from app.database import get_all_meetings, get_tags

meetings = get_all_meetings()
if meetings:
    latest = meetings[0]
    print(f'Latest meeting: {latest["filename"]}')
    print(f'Title: {latest["title"]}')
    print(f'Duration: {latest["duration"]}s')
    tags = get_tags(latest['filename'])
    print(f'Tags: {tags}')
    if tags:
        print('\n✓ TAGS SAVED SUCCESSFULLY!')
    else:
        print('\n✗ NO TAGS FOUND')
