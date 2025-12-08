# User Guide: Sync Data Flow and Reporting

## Overview

This guide explains how to use the sync features and reporting capabilities of the McRae's Website Analytics platform.

## Sync Operations

### Sync Modes

The platform supports two sync modes for each data source:

#### Complete Sync
- **When to use**: Initial onboarding or when you want to refresh all data
- **What it does**: Syncs all clients/campaigns/brands, regardless of whether they already exist in the database
- **Use cases**:
  - First-time setup
  - After a long period without syncing
  - When you want to ensure all data is up-to-date

#### New Sync
- **When to use**: Regular operations to pick up only new items
- **What it does**: Only syncs clients/campaigns/brands that don't already exist in the database
- **Use cases**:
  - Daily operations
  - Quick updates to pick up newly added items
  - Faster syncs when you only need new data

### Data Sources

#### Scrunch AI Data
- **Complete Sync**: Syncs all brands, prompts, and responses from Scrunch AI
- **New Sync**: Only syncs brands that don't exist in the database, then syncs prompts/responses for all existing brands
- **Typical duration**: ~30 minutes

#### GA4 (Google Analytics 4) Data
- **Complete Sync**: Syncs GA4 data for all clients with GA4 property IDs configured
- **New Sync**: Only syncs GA4 data for clients that don't have existing GA4 data
- **Typical duration**: Varies based on number of clients

#### Agency Analytics Data
- **Complete Sync**: Syncs all campaigns, rankings, keywords, and keyword rankings
- **New Sync**: Only syncs campaigns that don't exist in the database
- **Typical duration**: >2 hours (can be very long)

### Daily Auto Sync (Nightly)

The platform runs automatic syncs daily at 11:30 PM IST:
- **AgencyAnalytics**: All active clients (Complete mode)
- **GA4**: All clients with GA4 property ID mapped (Complete mode)
- **Scrunch**: All clients linked to Scrunch (Complete mode)

These syncs run in the background and don't require manual intervention. Check the Overview Dashboard to see sync status.

## Expected Behavior

### Initial Onboarding
1. Run **Complete Sync** for each data source to populate all data
2. This ensures you have a full dataset to work with
3. After initial sync, configure client mappings (GA4 property IDs, Scrunch brand IDs)

### Normal Operation
1. Rely on **nightly auto sync** for regular updates
2. The system automatically syncs all active clients daily
3. Monitor sync status on the Overview Dashboard

### Manual Syncs
- Use manual syncs only for exceptional cases:
  - After adding new clients/campaigns
  - When you need immediate data refresh
  - For troubleshooting data issues
- Prefer **New Sync** for faster operations during normal use
- Use **Complete Sync** when you need to refresh all data

## Reporting

### Shareable Reports

Each client can have a shareable public report URL:
- **Validity**: Links expire after 48 hours from creation
- **Regeneration**: Internal users can regenerate links to create new URLs and reset the 48-hour window
- **Customization**: 
  - Set custom report titles per client
  - Upload client logos
  - Configure branding and themes

### Report Features

- **GA4 Metrics**: Traffic overview, top pages, sources, geographic data, devices, conversions
- **Scrunch Data**: Top prompts, insights, KPIs
- **Agency Analytics**: Campaign rankings, keywords, search performance

## Best Practices

1. **Initial Setup**: Run Complete Sync for all data sources
2. **Regular Operations**: Let nightly auto sync handle updates
3. **Manual Syncs**: Use sparingly, prefer New Sync mode
4. **Monitoring**: Check Overview Dashboard for sync status
5. **Link Management**: Regenerate shareable links when they expire

## Troubleshooting

### Sync Taking Too Long
- Agency Analytics syncs can take >2 hours - this is normal
- Check sync status on Overview Dashboard
- Syncs run in background - you can continue using the app

### Link Expired
- Regenerate the shareable link from the Reporting Dashboard
- New link will be valid for 48 hours

### No Data Showing
- Verify client mappings (GA4 property ID, Scrunch brand ID)
- Check that syncs have completed successfully
- Ensure clients are marked as active

