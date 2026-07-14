# Queue System User Guide

## Overview

The Queue System is a workflow management interface for reviewing and processing documents in the PDFWEBSITE admin panel. It provides a structured way to manage document intake, field extraction, review sessions, and approval workflows.

## Key Features

- **File Queue Management**: Track documents through various statuses (pending, processing, review, approved, rejected, archived)
- **Field Extraction**: Automatically extract structured data from documents (text, dates, persons, organizations)
- **Review Sessions**: Start and end timed review sessions for quality assurance
- **Dynamic Field Definitions**: Configurable field types and validation rules
- **Assignment System**: Assign queue items to specific users for review
- **Statistics Dashboard**: Real-time metrics on queue performance and field accuracy

## Getting Started

### Accessing the Queue System

1. Log in to the admin panel at `http://localhost:8081/admin/login.php`
2. Navigate to **Queue** in the main menu
3. You'll see the main queue interface with all documents in the system

### Adding Files to the Queue

There are multiple ways to add files to the queue:

#### Method 1: From the Ingest Page
1. Go to `Admin → Ingest`
2. Browse to select a file from the local system
3. Click **Add to Queue**
4. The file will be added with status "pending"

#### Method 2: Via API
```bash
curl -X POST http://localhost:8081/admin/api/queue/add_item.php \
  -F "file=@/path/to/document.pdf" \
  -F "description=Public records request" \
  -F "priority=normal"
```

#### Method 3: Programmatically (PHP)
```php
$queueManager = new QueueManager();
$result = $queueManager->addToQueue('/path/to/file.pdf', [
    'description' => 'Test document',
    'priority' => 'high',
    'source' => 'manual_upload'
]);
```

## Queue Interface

### Main Queue View (`admin/queue.php`)

The main queue interface displays all queue items with the following columns:

- **ID**: Unique queue item identifier
- **Filename**: Name of the file
- **Status**: Current workflow status
- **Priority**: Importance level (low, normal, high, critical)
- **Assigned To**: User assigned to review
- **Created**: Date added to queue
- **Actions**: Quick actions for the item

#### Filtering and Sorting
- Use the status filter buttons to show only items with specific statuses
- Click column headers to sort by that column
- Use the search box to find items by filename or metadata

#### Bulk Actions
- Select multiple items using the checkboxes
- Choose bulk actions from the dropdown:
  - **Change Status**: Update status for all selected items
  - **Assign to User**: Assign selected items to a specific user
  - **Delete**: Remove items from queue (requires confirmation)

### Queue Item Detail View (`admin/queue_item.php`)

Click any queue item to view its detailed page with four main sections:

#### 1. File Information Panel (Left Column)
- **File Details**: Filename, path, size, MIME type, timestamps
- **Status & Actions**: Current status, priority, assignment, status change buttons
- **Field Statistics**: Counts of extracted, reviewed, accepted, and rejected fields
- **Quick Actions**: Extract fields, start review session, view/download file

#### 2. Extracted Fields Panel (Right Column)
- **Fields Table**: All extracted fields with values, confidence scores, and review status
- **Field Actions**: Accept/reject individual fields, edit field values
- **Bulk Field Actions**: Accept all or reject all fields

#### 3. Status History
- Timeline of all status changes with timestamps and user notes

#### 4. Review Sessions
- History of review sessions with duration and reviewer notes

## Workflow Management

### Standard Workflow

1. **File Upload** → Status: `pending`
2. **Field Extraction** → Status: `processing` (auto) → `review` (auto)
3. **Field Review** → Start review session, accept/reject fields
4. **Final Decision** → Status: `approved` or `rejected`
5. **Archiving** → Status: `archived` (completed items)

### Changing Status

To change a queue item's status:

1. On the queue item detail page, click the status button you want
2. Add optional notes about the status change
3. Click **Change Status**

Valid status transitions:
- `pending` → `processing`, `review`, `rejected`
- `processing` → `review`, `rejected`, `archived`
- `review` → `approved`, `rejected`, `pending`
- `approved` → `archived`
- `rejected` → `pending`, `archived`
- `archived` → `pending`, `review`

### Assignment System

Assign queue items to users for review:

1. On the queue item detail page, select a user from the "Change assignment..." dropdown
2. The item will appear in that user's assigned items list
3. Users can filter the main queue to show only items assigned to them

## Field Extraction and Review

### Extracting Fields

To extract fields from a document:

1. Navigate to the queue item detail page
2. Click the **Extract Fields** button
3. The system will analyze the document and extract:
   - Text fields (case codes, titles, descriptions)
   - Dates (filed dates, deadlines, document dates)
   - Persons (names, roles, contact information)
   - Organizations (names, types, addresses)
   - Case references and document types

### Reviewing Extracted Fields

1. **Start a Review Session**:
   - Click **Start Review Session** on the queue item detail page
   - A timer will track your review time
   - Your session will be recorded in the review history

2. **Review Individual Fields**:
   - Click the checkmark (✓) to accept a field
   - Click the X to reject a field
   - Click the pencil (✏️) to edit field value or add notes

3. **Bulk Field Actions**:
   - Use **Accept All** to accept all unreviewed fields
   - Use **Reject All** to reject all unreviewed fields

4. **End Review Session**:
   - Click **End Review Session** when finished
   - Add session notes if needed
   - The system will record your actions and session duration

### Field Types and Validation

The system supports several field types:

- **Text**: Plain text with optional length limits and patterns
- **Date**: Date values with validation and formatting
- **Number**: Numeric values with range validation
- **Select**: Dropdown with predefined options
- **Person**: Auto-complete from extracted persons database
- **Organization**: Auto-complete from extracted organizations
- **Case Reference**: Validation against existing case database

## Configuration

### Field Definitions

Field definitions are stored in `config/field_definitions.json`. Each field definition includes:

```json
{
  "field_name": "case_code",
  "display_name": "Case Code",
  "field_type": "text",
  "description": "Unique identifier for the case",
  "is_required": true,
  "validation_rules": ["required", "max:50"],
  "config": {
    "placeholder": "e.g., PRS-2024-001",
    "pattern": "^[A-Z0-9\\-]+$"
  },
  "group_id": 1,
  "display_order": 10
}
```

### Field Groups

Fields are organized into groups for better UI organization:

1. **Case Information**: Core case metadata
2. **Dates**: Important dates and deadlines
3. **District Information**: School district details
4. **Document Information**: Document metadata
5. **Person Information**: Extracted persons
6. **Organization Information**: Extracted organizations

### Queue Configuration

Queue behavior is configured in `config/queue_config.json`:

- **Status workflow**: Allowed status transitions
- **Priority weights**: Numeric weights for each priority level
- **Auto-processing**: Batch size and retry settings
- **Assignment**: Auto-assignment and workload balancing rules
- **File handling**: Size limits and allowed file types
- **Review**: Minimum review times and concurrent session limits

## User Roles and Permissions

### Available Roles

1. **Administrator**: Full access to all queue functions, field management, and system configuration
2. **Reviewer**: Can review queue items, extract fields, change statuses (except archival)
3. **Processor**: Can add files to queue and perform basic processing tasks
4. **Viewer**: Read-only access to queue and field information

### Permission Matrix

| Permission | Administrator | Reviewer | Processor | Viewer |
|------------|--------------|----------|-----------|--------|
| View queue | ✓ | ✓ | ✓ | ✓ |
| Add to queue | ✓ | ✓ | ✓ | ✗ |
| Extract fields | ✓ | ✓ | ✗ | ✗ |
| Review fields | ✓ | ✓ | ✗ | ✗ |
| Change status | ✓ | ✓ | Limited | ✗ |
| Assign items | ✓ | ✓ | ✗ | ✗ |
| Archive items | ✓ | ✗ | ✗ | ✗ |
| Manage fields | ✓ | ✗ | ✗ | ✗ |
| View statistics | ✓ | ✓ | ✓ | ✓ |

## Advanced Features

### API Integration

The queue system provides REST API endpoints:

- `GET /admin/api/queue/list.php` - List queue items with filtering
- `POST /admin/api/queue/add_item.php` - Add file to queue
- `POST /admin/api/queue/update_status.php` - Update queue item status
- `POST /admin/api/queue/extract_fields.php` - Extract fields from document
- `GET /admin/api/queue/stats.php` - Get queue statistics

### Real-time Updates

Enable real-time updates in `config/queue_config.json`:

```json
{
  "real_time_updates": {
    "enabled": true,
    "polling_interval": 30000,
    "websocket_url": "ws://localhost:8081/ws"
  }
}
```

### Custom Field Types

Create custom field types by extending the `FieldTypeInterface`:

1. Create a new PHP class in `admin/includes/fieldtypes/`
2. Implement the required methods: `validate()`, `renderInput()`, `renderDisplay()`
3. Register the field type in `FieldRegistry::registerFieldType()`

### Bulk Operations Script

Use the included test script to perform bulk operations:

```bash
php test_queue_workflow.php
```

This script tests:
- Database connectivity
- Queue table structure
- Field extraction functionality
- Field rendering capabilities
- Queue statistics retrieval

## Troubleshooting

### Common Issues

#### 1. "File too large" error
- Check `config/queue_config.json` → `file_handling.max_file_size_mb`
- Default limit is 50MB
- Increase limit or compress files before upload

#### 2. "Invalid file type" error
- Verify file extension is in allowed list
- Check `config/queue_config.json` → `file_handling.allowed_extensions`
- Add new extensions to the configuration if needed

#### 3. Field extraction fails
- Ensure the document contains extractable text (not scanned PDF)
- Check PHP memory limit (minimum 256MB recommended)
- Verify file permissions allow reading

#### 4. Database errors
- Run `scripts/check_database.php` to verify database structure
- Check database connection in `admin/includes/config.php`
- Ensure enhanced schema is loaded: `backend/enhanced_schema.sql`

#### 5. Performance issues with large queues
- Add database indexes on frequently queried columns
- Implement pagination for large result sets
- Enable query caching in `config/queue_config.json`

### Logs and Monitoring

- **Application logs**: Check PHP error log in Docker container
- **Database logs**: View via phpMyAdmin or MySQL logs
- **Queue statistics**: Available on admin dashboard
- **Field accuracy reports**: Generated after field extraction

## Best Practices

### For Administrators
1. **Regularly review queue statistics** to identify bottlenecks
2. **Monitor field extraction accuracy** and adjust field definitions as needed
3. **Archive completed items** to keep the queue manageable
4. **Backup field definitions** before making major changes
5. **Train users** on proper review procedures

### For Reviewers
1. **Start review sessions** for accurate time tracking
2. **Add detailed notes** when rejecting fields or changing status
3. **Use bulk actions** for efficient processing of similar items
4. **Check field confidence scores** before accepting/rejecting
5. **End review sessions** when taking breaks or switching tasks

### For Processors
1. **Add descriptive metadata** when uploading files
2. **Use appropriate priorities** (reserve "critical" for urgent items)
3. **Verify file readability** before adding to queue
4. **Group related documents** using tags or descriptions
5. **Follow naming conventions** for consistent extraction

## Migration and Backup

### Backing Up Queue Data

```sql
-- Export queue items
mysqldump -u username -p database_name intake_queue_items > queue_items_backup.sql

-- Export field definitions
mysqldump -u username -p database_name field_definitions > field_defs_backup.sql

-- Export extracted fields
mysqldump -u username -p database_name field_extractions > fields_backup.sql
```

### Restoring from Backup

```sql
-- Restore queue items
mysql -u username -p database_name < queue_items_backup.sql

-- Restore field definitions
mysql -u username -p database_name < field_defs_backup.sql

-- Restore extracted fields
mysql -u username -p database_name < fields_backup.sql
```

### Data Migration Checklist

1. Backup existing data
2. Update database schema (if needed)
3. Update configuration files
4. Test with a subset of data
5. Perform full migration during maintenance window
6. Verify data integrity post-migration

## Support and Resources

### Documentation
- [Architecture Overview](wiki/ARCHITECTURE.md)
- [Database Schema](backend/enhanced_schema.sql)
- [API Documentation](admin/api/README.md) - Coming soon
- [Field Type Development Guide](wiki/FIELD-TYPE-DEVELOPMENT.md) - Coming soon

### Training Materials
- Quick reference card (included in `docs/quick-reference.pdf`)
- Video tutorials (available on internal portal)
- Hands-on training sessions (monthly)

### Support Channels
- **System Issues**: Create issue in project repository
- **User Support**: Email support@example.com
- **Emergency Contact**: Call +1-555-123-4567 (24/7 for critical issues)

## Version History

### v1.0.0 (Current)
- Initial queue system implementation
- Basic field extraction and review
- User assignment system
- Statistics dashboard

### v1.1.0 (Planned)
- Advanced field types (nested, conditional)
- Real-time collaboration features
- Enhanced reporting and analytics
- Mobile-responsive interface

### v1.2.0 (Planned)
- Machine learning for field extraction
- Integration with external document systems
- Advanced workflow automation
- API webhook support

---

*Last updated: March 2024*  
*System version: 1.0.0*  
*Document version: 1.0*