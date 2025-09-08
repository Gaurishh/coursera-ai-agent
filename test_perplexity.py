from coursera_agent import run_agent

# Test with a single website
result = run_agent('nitdelhi.ac.in')

print('\n' + '='*60)
print('FINAL RESULTS:')
print('='*60)
print(f'Course: {result["course_recommendation"]["recommended_course"]}')
print(f'Reasoning: {result["course_recommendation"]["recommendation_reasoning"]}')
print(f'Score: {result["course_recommendation"]["recommendation_score"]}')

print(f'\nExtracted Contacts ({len(result["contact_info"]["contacts"])} found):')
print('-'*50)
for i, contact in enumerate(result['contact_info']['contacts'], 1):
    print(f'{i}. {contact.get("name", "Unknown")}')
    print(f'   Title: {contact.get("title", "No title")}')
    if contact.get('email'):
        print(f'   Email: {contact["email"]}')
    if contact.get('phone'):
        print(f'   Phone: {contact["phone"]}')
    print()
