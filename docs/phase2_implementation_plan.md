# Implementation Plan - Phase 2: Scalable Queue Management Interface

## Overview
Implement a scalable, configuration-driven queue management interface for the admin intake portal that supports dynamic field definitions, real-time updates, and extensible architecture for future enhancements.

This phase transforms the basic file browser into a comprehensive workflow management system with field-level review capabilities. The architecture is designed for scalability with a pluggable field system, configuration-driven UI components, and API-first design patterns. The system will support dynamic field addition, user-customizable views, and real-time collaboration features while integrating seamlessly with existing PHP/MySQL infrastructure and Python ingest pipelines.

## Types

### Core Data Types
**QueueItemExtended**: `{id: string, filename: string, filepath: string, mime_type: string, size: int, status: 'pending'|'processing'|'review'|'approved'|'rejected'|'archived', priority: 'low'|'normal'|'high'|'critical', assigned_to: int|null, assigned_user: {id: int, username: string, full_name: string}|null, created_at: datetime, updated_at: datetime, processed_at: datetime|null, review_notes: text|null, metadata: json, custom_fields: json, field_stats: {total: int, reviewed: int, accepted: int, rejected: int}, entity_stats: {persons: int, organizations: int, relationships: int}}`

**FieldDefinition**: `{field_id: string, field_name: string, display_name: string, type: 'text'|'date'|'number'|'person'|'organization'|'case_reference'|'document_type'|'custom', category: 'metadata'|'extracted'|'custom'|'entity', validation: {required: boolean, pattern: string|null, min: number|null, max: number|null, allowed_values: string[]|null}, ui: {component: string, icon: string, width: string, sortable: boolean, filterable: boolean, editable: boolean, group: string}, extraction: {parser: string|null, confidence_threshold: number|null}, version: int, active: boolean, created_at: datetime, updated_at: datetime}`

**FieldValue**: `{field_id: string, queue_item_id: int, value: string|number|date|json, confidence: float|null, source: 'parser'|'manual'|'ai'|'import', reviewed: boolean, accepted: boolean|null, reviewed_by: int|null, reviewed_at: datetime|null, validation_errors: string[], metadata: json, created_at: datetime, updated_at: datetime}`

**FieldGroup**: `{group_id: string, name: string, description: string, icon: string, fields: string[], display_order: int, collapsed_by_default: boolean, permissions: {view: string[], edit: string[]}}`

**UIViewConfiguration**: `{view_id: string, name: string, description: string, type: 'queue'|'review'|'dashboard', columns: {field_id: string, visible: boolean, width: string, sort_order: int|null, sort_direction: 'asc'|'desc'|null}[], filters: {field_id: string, operator: 'equals'|'contains'|'greater_than'|'less_than'|'between', value: any}[], user_id: int|null, is_default: boolean, created_at: datetime, updated_at: datetime}`

### Configuration Types
**SystemConfig**: `{field_registry: {auto_discover: boolean, scan_paths: string[], cache_ttl: int}, queue_ui: {default_view: string, refresh_interval: int, real_time_updates: boolean, batch_operations: boolean}, field_management: {allow_custom_fields: boolean, max_custom_fields: int, field_versioning: boolean}}`

**ValidationSchema**: `{schema_id: string, name: string, applies_to: string[], rules: {type: 'required'|'format'|'range'|'regex'|'custom', config: json, error_message: string, severity: 'error'|'warning'|'info'}[]}`

### API Types  
**APIResponse**: `{success: boolean, data: any, error: {code: string, message: string, details: json}|null, metadata: {timestamp: datetime, request_id: string, pagination: {total: int, page: int, per_page: int, pages: int}|null}}`

**WebhookEvent**: `{event_id: string, event_type: 'queue_item_created'|'queue_item_updated'|'field_extracted'|'field_reviewed'|'entity_linked', data: json, timestamp: datetime, source: string, attempts: int, status: 'pending'|'processed'|'failed'}`

## Files

### New Files
- `admin/queue.php` - Main queue management interface with dynamic columns, filtering, and bulk operations
- `admin/queue_item.php` - Detailed queue item view with tabbed interface for metadata, extracted fields, entities, and custom fields
- `admin/field_management.php` - UI for managing field definitions, groups, and validation rules
- `admin/queue_settings.php` - User preferences for queue views, column layouts, and filters
- `admin/api/fields.php` - REST API for field definition management and validation
- `admin/api/queue_operations.php` - API for queue operations (filter, sort, bulk actions)
- `admin/api/queue_views.php` - API for managing saved views and user preferences
- `admin/includes/FieldRegistry.php` - Central registry for field type discovery and management
- `admin/includes/FieldRenderer.php` - Dynamic field rendering based on field type and configuration
- `admin/includes/QueueUIManager.php` - Manages UI configurations, saved views, and user preferences
- `admin/includes/ValidationService.php` - Pluggable validation service with rule registry
- `admin/assets/js/queue.js` - Main queue interface JavaScript with DataTables integration
- `admin/assets/js/field_renderer.js` - Dynamic field rendering and validation in browser
- `admin/assets/js/queue_views.js` - Manage saved views and user preferences
- `admin/assets/js/bulk_operations.js` - Bulk action processing with progress tracking
- `admin/assets/css/queue_enhanced.css` - Enhanced CSS for queue interface
- `config/field_definitions.json` - Core field definitions and metadata
- `config/field_groups.json` - Field grouping for organized display
- `config/ui_defaults.json` - Default UI configurations and views
- `config/validation_schemas.json` - Validation rule schemas by field type
- `backend/field_sync.py` - Python script for synchronizing field definitions between systems

### Modified Files
- `admin/ingest.php` - Add "Add to Queue" button for files, integrate with queue system
- `admin/dashboard.php` - Add queue statistics widgets, recent activity feed, performance metrics
- `admin/includes/Database.php` - Add methods for dynamic field storage and retrieval
- `admin/includes/Auth.php` - Add permissions for field management and queue operations
- `admin/includes/QueueManager.php` - Extend with field-aware methods and bulk operations
- `admin/includes/FieldReview.php` - Integrate with FieldRegistry for dynamic field extraction
- `admin/includes/EntityManager.php` - Add field-based entity extraction hooks
- `admin/includes/header.php` - Add queue navigation item to main menu
- `admin/includes/config.php` - Add field registry configuration constants
- `backend/enhanced_schema.sql` - Add tables for field definitions, field values, and UI configurations
- `ingest_intake.py` - Auto-create queue items with field extraction based on definitions

### Configuration Files
- `.env` - Add field registry and queue UI configuration variables
- `docker-compose.yml` - Add optional real-time update service (Redis/WebSocket)

## Functions

### FieldRegistry.php
- `FieldRegistry::registerFieldType(string $type, FieldTypeInterface $handler): void` - Register new field type
- `FieldRegistry::getFieldDefinition(string $field_id): ?FieldDefinition` - Get field definition by ID
- `FieldRegistry::getFieldDefinitionsByCategory(string $category): array` - Get fields by category
- `FieldRegistry::getFieldRenderer(string $type): FieldRendererInterface` - Get renderer for field type
- `FieldRegistry::validateField(string $field_id, $value, array $context = []): ValidationResult` - Validate field value
- `FieldRegistry::scanFieldPlugins(string $directory): array` - Auto-discover field type plugins
- `FieldRegistry::getFieldGroups(): array` - Get organized field groups

### FieldRenderer.php
- `FieldRenderer::renderInput(FieldDefinition $field, $currentValue = null, array $options = []): string` - Render field input HTML
- `FieldRenderer::renderDisplay(FieldDefinition $field, $value, array $options = []): string` - Render field display HTML
- `FieldRenderer::renderFilter(FieldDefinition $field, $currentFilter = null): string` - Render filter control
- `FieldRenderer::getValidationRules(FieldDefinition $field): array` - Get validation rules for field
- `FieldRenderer::convertValue(FieldDefinition $field, $value, string $format): mixed` - Convert value between formats

### QueueUIManager.php
- `QueueUIManager::getDefaultView(string $viewType): UIViewConfiguration` - Get default view configuration
- `QueueUIManager::getUserView(int $userId, string $viewType): ?UIViewConfiguration` - Get user's saved view
- `QueueUIManager::saveUserView(int $userId, UIViewConfiguration $view): bool` - Save user view
- `QueueUIManager::getAvailableColumns(string $context): array` - Get available columns for context
- `QueueUIManager::applyViewToQuery(UIViewConfiguration $view, QueryBuilder $query): QueryBuilder` - Apply view filters to query
- `QueueUIManager::exportView(UIViewConfiguration $view): array` - Export view as array
- `QueueUIManager::importView(array $data): UIViewConfiguration` - Import view from array

### ValidationService.php
- `ValidationService::registerValidator(string $ruleType, ValidatorInterface $validator): void` - Register validator
- `ValidationService::validate(FieldDefinition $field, $value): ValidationResult` - Validate field value
- `ValidationService::validateMultiple(array $fields): array` - Validate multiple fields
- `ValidationService::getValidationErrors(FieldDefinition $field, $value): array` - Get validation errors
- `ValidationService::addCustomRule(string $name, callable $validator, string $errorMessage): void` - Add custom validation rule

### QueueManager.php (Extended)
- `QueueManager::getQueueItemsWithFields(array $filters, UIViewConfiguration $view, int $limit, int $offset): array` - Get queue items with field values
- `QueueManager::updateFieldValue(int $queueItemId, string $fieldId, $value, int $userId): bool` - Update field value
- `QueueManager::bulkUpdateFieldValues(array $queueItemIds, string $fieldId, $value, int $userId): BulkOperationResult` - Bulk update field values
- `QueueManager::getQueueItemWithFields(int $queueItemId): ?array` - Get queue item with all field values
- `QueueManager::searchQueueItems(string $query, array $fieldIds = []): array` - Search across queue items and fields

### FieldReview.php (Extended)
- `FieldReview::extractFieldsWithDefinitions(string $filepath, array $fieldDefinitions = []): array` - Extract fields using definitions
- `FieldReview::reviewFieldWithContext(int $fieldValueId, bool $accepted, int $userId, string $notes, array $context = []): bool` - Review field with context
- `FieldReview::getFieldExtractionStats(array $queueItemIds): array` - Get field extraction statistics
- `FieldReview::suggestFieldValues(int $queueItemId, array $fieldIds = []): array` - Suggest field values based on patterns

## Classes

### Core Classes
**FieldRegistry** - Central registry for field type discovery, registration, and management. Implements plugin pattern for extensibility.

**FieldTypeInterface** - Interface that all field type handlers must implement: `validate()`, `renderInput()`, `renderDisplay()`, `parseValue()`, `formatValue()`.

**FieldRenderer** - Dynamically renders field UI components based on field type and configuration. Supports themes and custom templates.

**ValidationService** - Pluggable validation service with rule registry. Supports custom validation rules and complex validation logic.

**QueueUIManager** - Manages UI configurations, saved views, user preferences, and applies them to data queries.

**BulkOperationProcessor** - Processes bulk operations with progress tracking, error handling, and rollback capabilities.

**RealTimeUpdateService** - Manages real-time updates via WebSockets or server-sent events for collaborative features.

### Field Type Implementations
**TextFieldType** - Handles text fields with options for multiline, rich text, and character limits.

**DateFieldType** - Handles date fields with date picker UI, range validation, and formatting options.

**NumberFieldType** - Handles numeric fields with precision, range validation, and unit display.

**PersonFieldType** - Handles person fields with auto-complete from extracted persons database.

**OrganizationFieldType** - Handles organization fields with auto-complete from extracted organizations.

**CaseReferenceFieldType** - Handles case references with validation against existing cases.

**SelectFieldType** - Handles select/dropdown fields with configurable options.

**MultiSelectFieldType** - Handles multi-select fields with tag interface.

### UI Component Classes
**DataTableManager** - Manages DataTables initialization, configuration, and interaction.

**FilterBuilder** - Builds complex filters from field definitions and user input.

**ColumnManager** - Manages dynamic column visibility, ordering, and formatting.

**ViewPersister** - Saves and loads user view preferences to database.

## Dependencies

### PHP Dependencies
- `ext-json` - Required for JSON field storage and configuration
- `ext-mbstring` - For proper Unicode text handling
- `ext-gd` or `ext-imagick` - For image processing in field types
- **Optional**: `composer require datatables/datatables` - For server-side processing
- **Optional**: `composer require nesbot/carbon` - For advanced date handling
- **Optional**: `composer require ramsey/uuid` - For UUID generation

### JavaScript Dependencies
- **DataTables 1.13+** - For advanced table functionality with dynamic columns
- **Select2 4.0+** - For enhanced select fields with search
- **Flatpickr** - For date/time picker fields
- **SortableJS** - For drag-and-drop column reordering
- **Chart.js** - For dashboard statistics charts
- **Alpine.js 3.0+** - For reactive UI components (lightweight alternative to Vue)
- **Pusher.js or Socket.io client** - For real-time updates (optional)

### Python Dependencies (for field sync)
- `PyMySQL` or `mysql-connector-python` - For database synchronization
- `jsonschema` - For validating field definition schemas
- `watchdog` - For monitoring configuration file changes

### Database Requirements
- **MySQL 8.0+** or **MariaDB 10.5+** - For JSON field support and window functions
- **Redis 6.0+** (optional) - For caching field definitions and real-time updates

## Testing

### Test Files
- `tests/FieldRegistryTest.php` - Unit tests for field registry functionality
- `tests/FieldRendererTest.php` - Unit tests for field rendering
- `tests/ValidationServiceTest.php` - Unit tests for validation service
- `tests/QueueUIManagerTest.php` - Unit tests for UI management
- `tests/integration/QueueWorkflowTest.php` - Integration tests for complete queue workflow
- `tests/integration/FieldManagementTest.php` - Integration tests for field management
- `tests/acceptance/QueueInterfaceTest.php` - Acceptance tests for queue interface
- `admin/assets/js/test/queue.test.js` - JavaScript unit tests for queue interface
- `backend/tests/field_sync_test.py` - Python tests for field synchronization

### Test Data
- `tests/fixtures/field_definitions/` - Sample field definition configurations
- `tests/fixtures/queue_items/` - Sample queue items with field values
- `tests/fixtures/documents/` - Sample documents for field extraction testing
- `tests/fixtures/user_views/` - Sample user view configurations

### Testing Strategy
1. **Unit Testing** - All PHP classes with PHPUnit, focusing on FieldRegistry and FieldRenderer
2. **Integration Testing** - Complete workflows including database interactions
3. **JavaScript Testing** - Queue interface functionality with Jest or similar
4. **Browser Testing** - UI components with Playwright or Selenium
5. **Performance Testing** - Load testing for queue with large datasets
6. **Security Testing** - Field validation and permission enforcement

## Implementation Order

### Week 1: Core Field System Foundation
1. **Database Updates** - Add tables for field definitions, field values, and UI configurations
2. **FieldRegistry Implementation** - Core field type registry with plugin system
3. **Basic Field Types** - Implement text, date, number field type handlers
4. **Validation Service** - Pluggable validation with core rules
5. **Database Layer** - Extended Database.php methods for dynamic field storage

### Week 2: Queue Management Interface
1. **Queue UI Framework** - Implement QueueUIManager and view persistence
2. **DataTables Integration** - Configure DataTables with dynamic columns
3. **Filter System** - Build filter builder and apply to queries
4. **Bulk Operations Framework** - Basic bulk status changes and assignments
5. **Queue Statistics** - Add queue stats to dashboard

### Week 3: Field Rendering and Review Interface
1. **FieldRenderer Implementation** - Dynamic input and display rendering
2. **Queue Item Detail View** - Tabbed interface with field groups
3. **Field Review Interface** - Inline field editing and validation
4. **Advanced Field Types** - Implement person, organization, select field types
5. **Field Extraction Integration** - Connect FieldReview with field definitions

### Week 4: Configuration and Management UI
1. **Field Management UI** - CRUD interface for field definitions
2. **View Management UI** - Save, load, and share view configurations
3. **User Preferences** - Per-user column layouts and filters
4. **Import/Export** - Field definition import/export functionality
5. **Configuration Validation** - Validate configuration files on load

### Week 5: API and Integration
1. **Field Management API** - REST endpoints for field definitions
2. **Queue Operations API** - API for queue filtering and operations
3. **Real-time Updates** - Optional WebSocket integration for collaboration
4. **Python Sync Script** - Field definition synchronization
5. **Integration Testing** - End-to-end testing of complete workflow

### Week 6: Polish and Optimization
1. **Performance Optimization** - Database indexing, query optimization
2. **Caching Strategy** - Field definition caching with invalidation
3. **Error Handling** - Comprehensive error handling and user feedback
4. **Accessibility** - WCAG compliance for UI components
5. **Documentation** - User guides and developer documentation

### Week 7: Advanced Features
1. **Custom Field Support** - UI for creating custom field types
2. **Field Dependencies** - Conditional field display based on other fields
3. **Field Versioning** - Support for field definition evolution
4. **Advanced Search** - Full-text search across all field values
5. **Reporting Integration** - Field-based reporting and analytics

### Week 8: Deployment and Migration
1. **Database Migration Scripts** - Safe migration from existing schema
2. **Configuration Migration** - Convert existing field extractions to new system
3. **User Training Materials** - Tutorials and help documentation
4. **Rollout Strategy** - Phased deployment with fallback options
5. **Monitoring Setup** - Performance monitoring and alerting

## Risk Mitigation

### Technical Risks
1. **Performance with Dynamic Fields** - Mitigation: JSON column indexing, query optimization, caching
2. **Complexity of Field System** - Mitigation: Incremental implementation, thorough testing
3. **Browser Compatibility** - Mitigation: Progressive enhancement, polyfills for older browsers
4. **Database Migration** - Mitigation: Comprehensive backup strategy, rollback plans

### Business Risks
1. **User Adoption** - Mitigation: User training, intuitive UI, gradual feature rollout
2. **Data Integrity** - Mitigation: Validation rules, audit logging, data backup
3. **System Downtime** - Mitigation: Staged deployment, fallback mechanisms

## Success Metrics
1. **Queue Processing Time** - Reduce average processing time by 30%
2. **Field Extraction Accuracy** - Achieve 95%+ accuracy on automated field extraction
3. **User Satisfaction** - 90%+ satisfaction score from admin users
4. **System Performance** - Sub-second response time for queue filtering
5. **Extensibility** - Ability to add new field types in under 2 hours

## Post-Implementation Roadmap
1. **Phase 3** - Entity linking and relationship management
2. **Phase 4** - Advanced analytics and reporting dashboard
3. **Phase 5** - Machine learning integration for smart field extraction
4. **Phase 6** - Mobile-responsive admin interface
5. **Phase 7** - API marketplace for third-party integrations