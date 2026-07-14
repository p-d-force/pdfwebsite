# Implementation Plan

Enhance the PHP admin intake portal with comprehensive workflow management, field-level review, entity linking, bulk operations, quality assurance, and advanced search capabilities to transform it into a complete document processing and review platform.

The current admin portal provides basic file browsing and case management but lacks sophisticated workflow automation, quality controls, and collaborative review features needed for large-scale document processing. This implementation will add queue-based processing, field-level data review, entity relationship management, bulk operations, and comprehensive analytics while maintaining the existing PHP/MySQL architecture and integrating with the Python ingest pipeline. The enhanced system will support team-based document review, automated validation, and seamless integration between manual review and automated processing.

[Types]  
Define comprehensive type system for queue management, field-level review, entity relationships, and quality metrics.

**Queue Types:**
- `IntakeQueueItem`: `{id: string, filename: string, filepath: string, mime_type: string, size: int, status: 'pending'|'processing'|'review'|'approved'|'rejected'|'archived', priority: 'low'|'normal'|'high'|'critical', assigned_to: int|null, created_at: datetime, updated_at: datetime, processed_at: datetime|null, review_notes: text|null, metadata: json}`
- `QueueStatusTransition`: `{id: string, queue_item_id: string, from_status: string, to_status: string, user_id: int, timestamp: datetime, notes: text, metadata: json}`
- `QueueFilter`: `{status: string[], priority: string[], assigned_to: int[], date_range: {start: datetime|null, end: datetime|null}, search: string|null}`

**Review Types:**
- `FieldExtraction`: `{id: string, queue_item_id: string, field_name: string, field_type: 'text'|'date'|'number'|'person'|'organization'|'case_reference'|'document_type', extracted_value: string, confidence: float, source: 'parser'|'manual'|'ai', reviewed: boolean, accepted: boolean|null, reviewed_by: int|null, reviewed_at: datetime|null, notes: text, validation_errors: string[]}`
- `ReviewSession`: `{id: string, queue_item_id: string, user_id: int, started_at: datetime, ended_at: datetime|null, actions: json, notes: text}`
- `ValidationRule`: `{id: string, name: string, description: text, field_type: string, rule_type: 'required'|'format'|'range'|'regex'|'lookup', rule_config: json, error_message: string, severity: 'error'|'warning'|'info', active: boolean}`

**Entity Types:**
- `EntityLink`: `{id: string, source_type: 'case'|'document'|'person'|'organization', source_id: string, target_type: 'case'|'document'|'person'|'organization', target_id: string, relationship_type: 'related_to'|'mentions'|'references'|'attached_to'|'authored_by'|'sent_to'|'received_from', confidence: float, verified: boolean, verified_by: int|null, verified_at: datetime|null, notes: text}`
- `ExtractedPerson`: `{id: string, name: string, role: string|null, organization: string|null, contact_info: json, extracted_from: string[], confidence: float, verified: boolean, merge_candidate_ids: string[]}`
- `ExtractedOrganization`: `{id: string, name: string, type: 'district'|'school'|'agency'|'company'|'other', extracted_from: string[], confidence: float, verified: boolean, district_code: string|null}`

**Bulk Operation Types:**
- `BulkOperation`: `{id: string, operation_type: 'status_change'|'tagging'|'assignment'|'export'|'delete', parameters: json, items_count: int, items_processed: int, status: 'pending'|'running'|'completed'|'failed', created_by: int, created_at: datetime, started_at: datetime|null, completed_at: datetime|null, error_message: text|null, result_summary: json}`
- `BulkOperationItem`: `{id: string, bulk_operation_id: string, item_id: string, item_type: 'queue_item'|'case'|'document', status: 'pending'|'processing'|'success'|'failed', error_message: text|null, processed_at: datetime|null, result_data: json}`

**Analytics Types:**
- `QualityMetric`: `{id: string, metric_name: string, metric_value: float, calculated_at: datetime, time_range: string, breakdown: json}`
- `UserPerformance`: `{user_id: int, period: string, items_reviewed: int, avg_review_time: float, accuracy_rate: float, completion_rate: float}`
- `SystemHealth`: `{timestamp: datetime, queue_size: int, pending_count: int, processing_count: int, avg_processing_time: float, error_rate: float, active_users: int}`

[Files]
Create new PHP files and modify existing files to implement comprehensive admin portal enhancements.

**New Files:**
- `admin/queue.php` - Main queue management interface with filtering, bulk actions, and status tracking
- `admin/queue_item.php` - Detailed view of individual queue items with field-level review interface
- `admin/bulk_operations.php` - Bulk operation management and monitoring
- `admin/analytics.php` - Quality assurance dashboard with metrics and reporting
- `admin/entity_linking.php` - Entity relationship management and visualization
- `admin/search_advanced.php` - Advanced search across all ingested content
- `admin/api/queue.php` - REST API for queue operations and automation
- `admin/api/analytics.php` - API for analytics data and reporting
- `admin/api/bulk_operations.php` - API for bulk operation management
- `admin/includes/QueueManager.php` - PHP class for queue management operations
- `admin/includes/FieldReview.php` - PHP class for field-level review operations
- `admin/includes/EntityManager.php` - PHP class for entity linking and management
- `admin/includes/BulkOperations.php` - PHP class for bulk operation processing
- `admin/includes/Analytics.php` - PHP class for metrics calculation and reporting
- `admin/assets/js/queue.js` - JavaScript for queue interface interactivity
- `admin/assets/js/field_review.js` - JavaScript for field-level review interface
- `admin/assets/js/entity_linking.js` - JavaScript for entity relationship visualization
- `admin/assets/css/admin_enhanced.css` - Additional CSS for enhanced interfaces
- `backend/queue_processor.py` - Python script for automated queue processing and validation
- `backend/entity_extractor.py` - Python script for automated entity extraction from documents

**Modified Files:**
- `admin/ingest.php` - Integrate with queue system, add queue status indicators, link to queue management
- `admin/dashboard.php` - Add queue statistics, recent activity, and performance metrics widgets
- `admin/cases.php` - Add entity relationship visualization, link to extracted entities
- `admin/includes/Database.php` - Add new table creation methods and query helpers for new entities
- `admin/includes/Auth.php` - Add permission checks for new queue and review functionalities
- `backend/schema.sql` - Add new tables for queue, review, entity, bulk operations, and analytics
- `backend/admin_schema.sql` - Add new tables for enhanced admin functionality
- `ingest_intake.py` - Update to create queue items automatically when new files are ingested
- `admin/.htaccess` - Ensure proper routing for new PHP files

**Configuration Files:**
- `config/queue_config.json` - Configuration for queue processing rules, status workflows, and validation
- `config/entity_types.json` - Configuration for entity types, relationships, and extraction rules
- `config/validation_rules.json` - Configuration for field validation rules and quality checks

[Functions]
Implement new PHP functions and modify existing ones to support enhanced functionality.

**New Functions in QueueManager.php:**
- `QueueManager::addToQueue($filepath, $metadata)` - Add file to processing queue
- `QueueManager::getQueueItems($filters, $limit, $offset)` - Retrieve queue items with filtering
- `QueueManager::updateQueueStatus($itemId, $newStatus, $userId, $notes)` - Update item status with audit trail
- `QueueManager::assignItem($itemId, $userId)` - Assign queue item to user
- `QueueManager::getQueueStats($timeRange)` - Calculate queue statistics and metrics
- `QueueManager::processBulkStatusChange($itemIds, $newStatus, $userId)` - Bulk status updates

**New Functions in FieldReview.php:**
- `FieldReview::extractFields($filepath, $extractionRules)` - Extract fields from document using configured parsers
- `FieldReview::getExtractedFields($queueItemId)` - Retrieve extracted fields for review
- `FieldReview::updateFieldReview($fieldId, $accepted, $userId, $notes)` - Update field review status
- `FieldReview::validateFields($fields, $validationRules)` - Validate extracted fields against rules
- `FieldReview::getReviewSession($queueItemId, $userId)` - Create or retrieve review session

**New Functions in EntityManager.php:**
- `EntityManager::extractEntities($text, $extractionRules)` - Extract entities from text content
- `EntityManager::linkEntities($sourceEntity, $targetEntity, $relationshipType)` - Create entity relationship
- `EntityManager::findDuplicateEntities($entity)` - Find potential duplicate entities
- `EntityManager::mergeEntities($primaryId, $mergeIds)` - Merge duplicate entities
- `EntityManager::getEntityGraph($entityId, $depth)` - Retrieve entity relationship graph
- `EntityManager::searchEntities($query, $entityTypes)` - Search across extracted entities

**New Functions in BulkOperations.php:**
- `BulkOperations::createOperation($operationType, $parameters, $itemIds, $userId)` - Create bulk operation
- `BulkOperations::processOperation($operationId)` - Process bulk operation items
- `BulkOperations::getOperationStatus($operationId)` - Get operation progress and status
- `BulkOperations::cancelOperation($operationId)` - Cancel running operation
- `BulkOperations::getOperationHistory($filters)` - Retrieve operation history

**New Functions in Analytics.php:**
- `Analytics::calculateQueueMetrics($timeRange)` - Calculate queue performance metrics
- `Analytics::calculateUserPerformance($userId, $timeRange)` - Calculate user review performance
- `Analytics::calculateQualityMetrics($timeRange)` - Calculate data quality metrics
- `Analytics::generateReport($reportType, $parameters)` - Generate formatted reports
- `Analytics::getSystemHealth()` - Get current system health indicators

**Modified Functions:**
- `Auth::requirePermission($permission)` - Extended to check specific queue/review permissions
- `Database::createTables()` - Extended to create new queue, entity, and analytics tables
- `ingest_intake::ingest()` - Modified to automatically create queue items for processed files

[Classes]
Implement new PHP classes and extend existing ones for enhanced functionality.

**New Classes:**
- `QueueManager` - Handles all queue-related operations, status transitions, and statistics
- `FieldReview` - Manages field extraction, review workflows, and validation
- `EntityManager` - Handles entity extraction, linking, deduplication, and relationship management
- `BulkOperations` - Manages bulk operation processing, monitoring, and history
- `Analytics` - Calculates metrics, generates reports, and provides system health data
- `QueueItem` - Data model representing a queue item with status and metadata
- `ExtractedField` - Data model representing an extracted field with review status
- `EntityRelationship` - Data model representing entity relationships
- `BulkOperation` - Data model representing a bulk operation with progress tracking

**Extended Classes:**
- `Auth` - Add permission-based access control for new queue and review features
- `Database` - Add methods for new table schemas and complex queries
- `CaseManager` (if exists) - Integrate with entity linking system

[Dependencies]
Add new PHP dependencies and Python packages for enhanced functionality.

**PHP Dependencies:**
- `ext-json` - Already required, used extensively for new JSON data structures
- `ext-mbstring` - For proper text processing with multi-byte characters
- `ext-gd` or `ext-imagick` - For improved image processing and thumbnail generation
- Consider adding: `smalot/pdfparser` for PDF text extraction (via Composer if not already)

**Python Dependencies (for enhanced processing):**
- `pdfminer.six` - For advanced PDF text extraction
- `python-docx` - For DOCX document parsing
- `openpyxl` or `pandas` - For spreadsheet processing
- `python-pptx` - For PowerPoint presentation parsing
- `spacy` or `nltk` - For NLP-based entity extraction (optional enhancement)

**JavaScript Dependencies:**
- `Chart.js` or `D3.js` - For analytics dashboard charts and visualizations
- `Vis.js` or `Cytoscape.js` - For entity relationship graph visualization
- `DataTables` - For enhanced table functionality with sorting/filtering

[Testing]
Implement comprehensive testing for new functionality and modifications.

**Test Files:**
- `tests/QueueManagerTest.php` - Unit tests for queue management functionality
- `tests/FieldReviewTest.php` - Unit tests for field extraction and review
- `tests/EntityManagerTest.php` - Unit tests for entity management
- `tests/BulkOperationsTest.php` - Unit tests for bulk operations
- `tests/AnalyticsTest.php` - Unit tests for analytics and reporting
- `tests/integration/QueueWorkflowTest.php` - Integration tests for complete queue workflow
- `backend/tests/queue_processor_test.py` - Python tests for queue processing
- `backend/tests/entity_extractor_test.py` - Python tests for entity extraction

**Test Data:**
- Create test document files in `tests/fixtures/` for various file types (PDF, DOCX, XLSX, etc.)
- Create test database with sample queue items, extracted fields, and entities
- Generate test reports and analytics output for validation

**Testing Strategy:**
- Unit tests for all new PHP classes and methods
- Integration tests for complete workflows (upload → queue → extraction → review → approval)
- Performance tests for bulk operations with large datasets
- Security tests for permission enforcement and data access controls
- Browser tests for new UI components using PHPUnit or similar framework

[Implementation Order]
Execute implementation in logical phases to minimize disruption and ensure successful integration.

1. **Phase 1: Database Schema and Core Classes** (Week 1)
   - Create new database tables for queue, fields, entities, bulk operations, analytics
   - Implement QueueManager, FieldReview, EntityManager, BulkOperations, Analytics PHP classes
   - Update Database.php with new table creation methods
   - Create basic unit tests for core classes

2. **Phase 2: Queue Management Interface** (Week 2)
   - Implement admin/queue.php with filtering, sorting, and status management
   - Implement admin/queue_item.php with basic item details view
   - Create queue.js for interactive queue interface
   - Integrate queue system into existing admin/ingest.php
   - Update dashboard.php with queue statistics widgets

3. **Phase 3: Field-Level Review Interface** (Week 3)
   - Implement field extraction backend in FieldReview class
   - Create field review interface in queue_item.php
   - Implement field validation and acceptance workflows
   - Add field_review.js for interactive review interface
   - Integrate with Python extraction scripts for automated field extraction

4. **Phase 4: Entity Linking and Management** (Week 4)
   - Implement entity extraction and linking in EntityManager class
   - Create admin/entity_linking.php interface
   - Implement entity relationship visualization with JavaScript library
   - Add entity search and deduplication features
   - Integrate entity system with existing case management

5. **Phase 5: Bulk Operations and Automation** (Week 5)
   - Implement BulkOperations class for processing bulk actions
   - Create admin/bulk_operations.php interface
   - Add bulk status changes, assignments, tagging, and exports
   - Implement API endpoints for programmatic bulk operations
   - Create backend/queue_processor.py for automated processing

6. **Phase 6: Analytics and Quality Assurance** (Week 6)
   - Implement Analytics class for metrics calculation
   - Create admin/analytics.php dashboard with charts and reports
   - Add quality metrics, user performance tracking, system health monitoring
   - Implement configurable validation rules and quality checks
   - Create export functionality for reports

7. **Phase 7: Advanced Search and Integration** (Week 7)
   - Implement admin/search_advanced.php with full-text search across all content
   - Add OCR/text extraction integration for searchable document content
   - Enhance API with webhook support and external system integration
   - Implement user collaboration features (notes, comments, assignments)
   - Final integration testing and performance optimization

8. **Phase 8: Documentation and Deployment** (Week 8)
   - Create user documentation for new features
   - Update admin help text and tooltips
   - Perform security audit and penetration testing
   - Create deployment scripts and migration procedures
   - Final user acceptance testing and bug fixes