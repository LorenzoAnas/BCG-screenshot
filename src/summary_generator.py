def display_final_summary(event_categories_summary):
    """Display final summary of event categories across all servers."""
    if not event_categories_summary:
        print("\n📋 No events processed for summary")
        return
    
    print("\n" + "="*60)
    print("📋 FINAL SUMMARY - Event Categories Across All Servers")
    print("="*60)
    
    total_events = sum(cat['count'] for cat in event_categories_summary.values())
    total_servers = len(set().union(*[cat['servers'] for cat in event_categories_summary.values()]))
    
    print(f"Total Events Processed: {total_events}")
    print(f"Total Servers Analyzed: {total_servers}")
    print(f"Event Categories Found: {len(event_categories_summary)}")
    print("\nBreakdown by Category:")
    print("-" * 60)
    
    # Sort categories by count (descending)
    sorted_categories = sorted(
        event_categories_summary.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    
    for category, data in sorted_categories:
        servers_list = sorted(list(data['servers']))
        percentage = (data['count'] / total_events) * 100 if total_events > 0 else 0
        
        print(f"📌 {category}")
        print(f"   Count: {data['count']} events ({percentage:.1f}%)")
        print(f"   Servers: {', '.join(servers_list)}")
        print()
    
    print("="*60)
