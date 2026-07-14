# Implementation Plan - Phase 3: Comprehensive Entity Management System

## Overview
Implement a comprehensive entity management system that transforms extracted entities into a connected knowledge graph with visual interfaces for linking, deduplication, verification, and relationship analysis.

This phase builds upon the existing EntityManager foundation and Phase 2 queue system to create a complete entity lifecycle management platform. The system will provide visual tools for managing the relationships between cases, documents, persons, and organizations, transforming raw extracted data into a structured knowledge graph. Key innovations include intelligent deduplication with confidence scoring, interactive relationship visualization, NLP-enhanced entity extraction, and integrated verification workflows that connect directly to the queue review process.

## Types

### Core Entity Types
**EntityNode**: `{entity_id: string, entity_type: 'person'|'organization'|'case'|'document'|'message'|'event', display_name: string, properties: json, extracted_from: json[], confidence: float, verified: boolean, verification_history: VerificationRecord[], merge_candidates: string[], created_at: datetime, updated_at: datetime, last_extracted_at: datetime, source_count: int, relationship_count: int}`

**EntityRelationship**: `{relationship_id: string, source_entity_id: string, target_entity_id: string, relationship_type: 'mentions'|'authored_by'|'sent_to'|'received_from'|'belongs_to'|'related_to'|'references'|'attached_to'|'derived_from', properties: json, confidence: float, verified: boolean, verification_history: VerificationRecord[], extracted_from: json[], created_at: datetime, updated_at: datetime, weight: float, directional: boolean}`

**VerificationRecord**: `{verification_id: string, entity_id: string, user_id: int, action: 'verify'|'unverify'|'merge'|'split'|'link'|'unlink', status_before: json, status_after: json, notes: string, timestamp: datetime, confidence_change: float, related_entities: string[]}`

**EntityExtractionResult**: `{extraction_id: string, source_id: string, source_type: 'document'|'message'|'queue_item', entity_type: string, entities: EntityCandidate[], extraction_method: 'regex'|'nlp'|'ai'|'manual', confidence_scores: {overall: float, per_entity: json}, processing_time_ms: int, metadata: json, created_at: datetime}`

**EntityCandidate**: `{candidate_id: string, entity_type: string, display_name: string, raw_text: string, context: string, extracted_properties: json, confidence: float, position: {start: int, end: int, sentence: int, paragraph: int}, suggested_links: SuggestedLink[], duplicate_check: DuplicateCheckResult, validation_status: 'pending'|'valid'|'invalid'|'needs_review'}`

### Configuration Types
**EntityExtractionConfig**: `{config_id: string, entity_type: string, extraction_methods: {method: string, priority: int, config: json}[], validation_rules: ValidationRule[], confidence_thresholds: {low: float, medium: float, high: float}, post_processing: {deduplication: boolean, linking: boolean, verification_prompt: boolean}, enabled: boolean, version: int}`

**DeduplicationRule**: `{rule_id: string, entity_type: string, matching_strategy: 'exact'|'fuzzy'|'semantic', fields: {field_name: string, weight: float, similarity_threshold: float}[], overall_threshold: float, auto_merge_threshold: float, review_threshold: float, enabled: boolean}`

**VisualizationConfig**: `{config_id: string, layout_algorithm: 'force'|'hierarchical'|'circular'|'grid', node_size: {base: float, by_type: json, by_relationship_count: boolean}, edge_style: {width: {base: float, by_weight: boolean}, color: {by_type: boolean, palette: string[]}}, filters: {min_confidence: float, verified_only: boolean, entity_types: string[], max_nodes: int}, interactions: {zoom: boolean, pan: boolean, drag: boolean, click: boolean, hover: boolean}}`

### API Types
**EntitySearchRequest**: `{query: string, entity_types: string[], filters: {confidence_min: float, verified_only: boolean, has_relationships: boolean}, pagination: {page: int, per_page: int, sort_by: string, sort_order: 'asc'|'desc'}, include_relationships: boolean, relationship_depth: int}`

**EntitySearchResponse**: `{results: EntityNode[], total: int, pagination: {page: int, per_page: int, pages: int}, facets: {by_type: json, by_confidence: json, by_verification_status: json}, suggested_queries: string[], processing_time_ms: int}`

**BulkEntityOperation**: `{operation_id: string, operation_type: 'merge'|'verify'|'link'|'export', entity_ids: string[], parameters: json, status: 'pending'|'processing'|'completed'|'failed', created_by: int, created_at: datetime, started_at: datetime|null, completed_at: datetime|null, results: json, error: string|null}`

## Files

### New Files
- `admin/entities.php` - Main entity management dashboard with search, filtering, and bulk operations
- `admin/entity_detail.php` - Detailed entity view with relationships, extraction sources, and verification history
- `admin/entity_linking.php` - Visual interface for linking entities with drag-and-drop and relationship type selection
- `admin/entity_deduplication.php` - Deduplication workspace with side-by-side comparison and merge tools
- `admin/entity_graph.php` - Interactive relationship graph visualization with filtering and exploration
- `admin/entity_extraction_config.php` - Configuration interface for entity extraction rules and NLP settings
- `admin/api/entities/search.php` - Entity search API with faceting and relationship inclusion
- `admin/api/entities/link.php` - API for creating and managing entity relationships
- `admin/api/entities/merge.php` - API for entity deduplication and merging operations
- `admin/api/entities/verify.php` - API for entity verification workflows
- `admin/api/entities/graph.php` - API for graph data generation and visualization
- `admin/includes/EntityEnhanced.php` - Enhanced entity management with NLP integration and advanced features
- `admin/includes/EntityDeduplication.php` - Deduplication engine with fuzzy matching and confidence scoring
- `admin/includes/EntityVisualization.php` - Graph visualization data preparation and layout algorithms
- `admin/includes/NLPExtractor.php` - NLP-based entity extraction using spaCy/StanfordNLP patterns
- `admin/includes/EntityVerificationWorkflow.php` - Verification workflow management with audit trails
- `admin/assets/js/entities.js` - Main entity management interface JavaScript
- `admin/assets/js/entity_graph.js` - Interactive graph visualization using D3.js/Vis.js
- `admin/assets/js/entity_linking.js` - Drag-and-drop linking interface JavaScript
- `admin/assets/js/entity_deduplication.js` - Deduplication comparison and merge interface
- `admin/assets/css/entities.css` - Entity management interface styles
- `admin/assets/css/entity_graph.css` - Graph visualization styles
- `config/entity_extraction_rules.json` - Configuration for entity extraction methods and rules
- `config/deduplication_rules.json` - Deduplication matching rules and thresholds
- `config/entity_visualization.json` - Graph visualization configuration
- `config/nlp_models.json` - NLP model configurations and paths
- `scripts/train_entity_model.py` - Python script for training custom entity extraction models
- `scripts/sync_entities_to_graph.py` - Synchronization between database entities and JSON graph files

### Modified Files
- `admin/includes/EntityManager.php` - Enhance with new methods for visualization, NLP extraction, and workflow integration
- `admin/queue_item.php` - Add entity linking panel and entity extraction results display
- `admin/dashboard.php` - Add entity statistics widgets and relationship insights
- `admin/includes/Database.php` - Add methods for entity graph queries and relationship traversals
- `admin/includes/FieldReview.php` - Integrate entity extraction during field review process
- `admin/includes/QueueManager.php` - Add entity extraction triggers on queue item processing
- `admin/includes/FieldRegistry.php` - Register entity field types with enhanced extraction capabilities
- `backend/enhanced_schema.sql` - Add tables for entity verification, extraction history, and graph metadata
- `ingest_intake.py` - Integrate enhanced entity extraction during document ingestion
- `wiki/INGEST-ENTITY-GRAPH.md` - Update with new entity types, relationships, and management workflows

### Configuration Files
- `.env` - Add NLP model paths, entity extraction configuration, and visualization settings
- `docker-compose.yml` - Add optional NLP service container (spaCy/StanfordNLP server)

## Functions

### EntityEnhanced.php
- `EntityEnhanced::extractWithNLP(string $text, array $config): EntityExtractionResult` - Extract entities using NLP models
- `EntityEnhanced::getEntityGraph(string $entityId, int $depth, array $filters): array` - Get enhanced relationship graph with filtering
- `EntityEnhanced::suggestRelationships(string $entityId, array $candidateIds): array` - Suggest potential relationships based on patterns
- `EntityEnhanced::calculateEntityCentrality(string $entityId): array` - Calculate graph centrality metrics for entity
- `EntityEnhanced::findRelationshipPaths(string $sourceId, string $targetId, int $maxDepth): array` - Find all paths between entities
- `EntityEnhanced::batchExtractEntities(array $texts, array $config): array` - Batch entity extraction with parallel processing
- `EntityEnhanced::enrichEntityWithExternalData(string $entityId, array $sources): array` - Enrich entity with external data sources

### EntityDeduplication.php
- `EntityDeduplication::findPotentialDuplicates(string $entityId, array $rules): array` - Find potential duplicates using configurable rules
- `EntityDeduplication::calculateSimilarity(EntityNode $entity1, EntityNode $entity2, array $rules): float` - Calculate similarity score between entities
- `EntityDeduplication::mergeEntities(array $entityIds, string $primaryId, array $mergeStrategy): MergeResult` - Merge entities with configurable strategy
- `EntityDeduplication::suggestMergeCandidates(array $entities, float $threshold): array` - Suggest merge candidates based on similarity
- `EntityDeduplication::validateMerge(EntityNode $primary, array $mergeEntities): ValidationResult` - Validate merge operation for consistency
- `EntityDeduplication::createMergePreview(array $entityIds): MergePreview` - Create preview of merge results
- `EntityDeduplication::undoMerge(string $mergeOperationId): bool` - Undo a merge operation

### EntityVisualization.php
- `EntityVisualization::generateGraphData(array $entityIds, array $config): GraphData` - Generate graph data for visualization
- `EntityVisualization::calculateLayout(GraphData $graph, string $algorithm): LayoutResult` - Calculate graph layout using specified algorithm
- `EntityVisualization::applyFilters(GraphData $graph, array $filters): GraphData` - Apply filters to graph data
- `EntityVisualization::exportGraph(GraphData $graph, string $format): string` - Export graph in various formats (JSON, GraphML, GEXF)
- `EntityVisualization::findCommunities(GraphData $graph): array` - Detect communities/clusters in the graph
- `EntityVisualization::calculateMetrics(GraphData $graph): GraphMetrics` - Calculate graph metrics (density, diameter, centrality)
- `EntityVisualization::generateTimeline(array $entityIds, string $timeField): TimelineData` - Generate timeline visualization data

### NLPExtractor.php
- `NLPExtractor::initializeModel(string $modelName): bool` - Initialize NLP model
- `NLPExtractor::extractNamedEntities(string $text): array` - Extract named entities using NLP
- `NLPExtractor::extractRelationships(string $text): array` - Extract relationships between entities in text
- `NLPExtractor::classifyEntity(string $text, string $entity): string` - Classify entity type using NLP
- `NLPExtractor::extractCoreferenceChains(string $text): array` - Extract coreference chains (pronoun resolution)
- `NLPExtractor::trainCustomModel(array $trainingData, array $config): TrainingResult` - Train custom entity extraction model
- `NLPExtractor::evaluateModel(array $testData): EvaluationResult` - Evaluate model performance

### EntityVerificationWorkflow.php
- `EntityVerificationWorkflow::createVerificationTask(string $entityId, int $userId, string $reason): string` - Create verification task
- `EntityVerificationWorkflow::getPendingVerifications(array $filters): array` - Get pending verification tasks
- `EntityVerificationWorkflow::submitVerification(string $taskId, bool $verified, string $notes, array $evidence): bool` - Submit verification result
- `EntityVerificationWorkflow::getVerificationHistory(string $entityId): array` - Get entity verification history
- `EntityVerificationWorkflow::calculateVerificationScore(string $entityId): float` - Calculate verification confidence score
- `EntityVerificationWorkflow::escalateVerification(string $taskId, int $toUserId, string $reason): bool` - Escalate verification task
- `EntityVerificationWorkflow::getVerificationStatistics(array $filters): array` - Get verification statistics

### EntityManager.php (Enhanced)
- `EntityManager::linkEntitiesWithVisual(string $sourceId, string $targetId, string $relationshipType, array $properties, float $confidence): array` - Enhanced linking with visual feedback
- `EntityManager::searchEntitiesAdvanced(EntitySearchRequest $request): EntitySearchResponse` - Advanced search with faceting
- `EntityManager::exportEntityGraph(array $entityIds, string $format): string` - Export entity graph
- `EntityManager::importEntityGraph(string $data, string $format, array $options): array` - Import entity graph
- `EntityManager::getEntityStatisticsDetailed(array $filters): array` - Detailed entity statistics
- `EntityManager::cleanupOrphanedEntities(array $options): CleanupResult` - Cleanup orphaned entities
- `EntityManager::backupEntityGraph(string $backupId): bool` - Backup entity graph

## Classes

### Core Entity Classes
**EntityEnhanced** - Main enhanced entity management class with NLP integration, graph analysis, and advanced search capabilities.

**EntityDeduplication** - Deduplication engine supporting multiple matching strategies (exact, fuzzy, semantic), confidence scoring, and merge operations with audit trails.

**EntityVisualization** - Graph visualization system with multiple layout algorithms, filtering, and export capabilities for relationship analysis.

**NLPExtractor** - NLP integration layer supporting spaCy, StanfordNLP, or custom models for advanced entity and relationship extraction.

**EntityVerificationWorkflow** - Complete verification workflow management with task assignment, escalation, evidence tracking, and confidence scoring.

**EntityGraphImporter** - Import/export functionality for entity graphs supporting multiple formats (JSON, GraphML, GEXF, Neo4j).

### UI Component Classes
**EntitySearchInterface** - Advanced search interface with faceting, auto-complete, and relationship-aware filtering.

**EntityLinkingInterface** - Drag-and-drop linking interface with relationship type selection and confidence scoring.

**EntityComparisonInterface** - Side-by-side entity comparison for deduplication with highlight differences and merge preview.

**GraphVisualizationInterface** - Interactive D3.js/Vis.js based graph visualization with zoom, pan, filtering, and node/edge styling.

**VerificationWorkflowInterface** - Task-based verification interface with evidence attachment, note-taking, and escalation paths.

### Service Classes
**EntityExtractionPipeline** - Orchestrates extraction pipeline combining regex, NLP, and AI methods with confidence aggregation.

**RelationshipMiningService** - Mines relationships from text using co-occurrence analysis, syntactic patterns, and semantic similarity.

**EntityEnrichmentService** - Enriches entities with external data sources (Wikipedia, LinkedIn, organizational databases).

**GraphAnalysisService** - Performs graph analysis including centrality, community detection, and path finding.

**AuditTrailService** - Maintains complete audit trail for all entity operations (create, update, merge, verify, link).

## Dependencies

### PHP Dependencies
- `ext-json` - Required for JSON entity storage and configuration
- `ext-mbstring` - For proper Unicode text handling in entity extraction
- `ext-curl` - For external API calls to enrichment services
- **Optional**: `composer require guzzlehttp/guzzle` - For HTTP client functionality
- **Optional**: `composer require monolog/monolog` - For enhanced logging
- **Optional**: `composer require league/csv` - For entity export/import
- **Optional**: `composer require symfony/process` - For NLP model execution

### JavaScript Dependencies
- **D3.js 7.0+** - For interactive graph visualization
- **Vis.js 9.0+** - Alternative graph visualization library
- **Alpine.js 3.0+** - For reactive UI components
- **SortableJS** - For drag-and-drop entity linking
- **Diff2Html** - For entity comparison in deduplication interface
- **Chart.js** - For entity statistics and metrics
- **Select2** - For enhanced entity selection

### Python Dependencies (NLP/ML)
- `spacy` - For NLP-based entity extraction and relationship mining
- `nltk` - For text processing and tokenization
- `scikit-learn` - For machine learning and similarity calculations
- `gensim` - For semantic similarity and topic modeling
- `transformers` (Hugging Face) - For transformer-based entity extraction
- `pandas` - For data processing and analysis
- `networkx` - For graph analysis and metrics calculation

### External Services
- **spaCy models** (`en_core_web_sm`, `en_core_web_lg`) - Pre-trained NLP models
- **StanfordNLP** - Alternative NLP pipeline (optional)
- **Wikipedia API** - For entity enrichment (optional)
- **OpenCorporates API** - For organization data enrichment (optional)
- **Redis** - For caching entity extraction results and graph data

### Database Requirements
- **MySQL 8.0+** or **MariaDB 10.5+** - For JSON field support and window functions
- **Full-text search indexes** - For entity search performance
- **Graph database** (optional: Neo4j, ArangoDB) - For advanced graph queries (can be added later)

## Testing

### Test Files
- `tests/EntityEnhancedTest.php` - Unit tests for enhanced entity management
- `tests/EntityDeduplicationTest.php` - Unit tests for deduplication engine
- `tests/EntityVisualizationTest.php` - Unit tests for visualization system
- `tests/NLPExtractorTest.php` - Unit tests for NLP extraction
- `tests/EntityVerificationWorkflowTest.php` - Unit tests for verification workflows
- `tests/integration/EntityManagementTest.php` - Integration tests for complete entity management
- `tests/integration/EntityGraphTest.php` - Integration tests for graph functionality
- `tests/acceptance/EntityInterfaceTest.php` - Acceptance tests for entity interfaces
- `admin/assets/js/test/entities.test.js` - JavaScript tests for entity interface
- `backend/tests/entity_extraction_test.py` - Python tests for entity extraction
- `backend/tests/graph_analysis_test.py` - Python tests for graph analysis

### Test Data
- `tests/fixtures/entities/` - Sample entity data for testing
- `tests/fixtures/documents/` - Sample documents for entity extraction testing
- `tests/fixtures/relationships/` - Sample relationship data
- `tests/fixtures/nlp_models/` - Sample NLP models for testing
- `tests/fixtures/graphs/` - Sample graph data for visualization testing

### Testing Strategy
1. **Unit Testing** - All PHP classes with PHPUnit, focusing on EntityEnhanced and EntityDeduplication
2. **Integration Testing** - Complete entity workflows including database and NLP integration
3. **JavaScript Testing** - Entity interface functionality with Jest/Cypress
4. **NLP Model Testing** - Accuracy testing for entity extraction models
5. **Performance Testing** - Load testing for entity search and graph visualization
6. **Usability Testing** - User testing for entity linking and deduplication interfaces
7. **Security Testing** - Access control testing for entity management operations

## Implementation Order

### Week 1-2: Enhanced Entity Foundation
1. **Database Schema Enhancements** - Add tables for entity verification, extraction history, and graph metadata
2. **EntityEnhanced Class** - Build enhanced entity management with NLP integration hooks
3. **Advanced Search Implementation** - Implement faceted search with relationship inclusion
4. **Entity Extraction Pipeline** - Create orchestration layer for multiple extraction methods
5. **Basic Entity Visualization** - Initial graph data generation and simple visualization

### Week 3-4: Deduplication and Verification
1. **EntityDeduplication Engine** - Implement fuzzy matching, similarity scoring, and merge operations
2. **Deduplication Interface** - Create UI for side-by-side comparison and merge tools
3. **Verification Workflow System** - Build task-based verification with audit trails
4. **Verification Interface** - Create UI for verification tasks and evidence management
5. **Entity Statistics Dashboard** - Enhanced statistics and quality metrics

### Week 5-6: Visualization and Linking
1. **EntityVisualization System** - Implement graph layout algorithms and filtering
2. **Interactive Graph Interface** - Build D3.js/Vis.js based graph visualization
3. **Entity Linking Interface** - Create drag-and-drop linking with relationship type selection
4. **Relationship Mining Service** - Implement co-occurrence analysis and pattern mining
5. **Graph Analysis Tools** - Add centrality, community detection, and path finding

### Week 7-8: NLP Integration and Advanced Features
1. **NLPExtractor Integration** - Integrate spaCy/StanfordNLP for advanced entity extraction
2. **NLP Configuration Interface** - Create UI for managing NLP models and rules
3. **Entity Enrichment Service** - Add external data source integration
4. **Import/Export Functionality** - Implement multiple format support for entity graphs
5. **Performance Optimization** - Caching, indexing, and query optimization

### Week 9-10: Polish and Integration
1. **Queue Integration** - Connect entity extraction to queue item processing
2. **Field Review Integration** - Add entity panels to field review interface
3. **Dashboard Widgets** - Add entity insights to admin dashboard
4. **API Development** - Complete REST API for all entity operations
5. **Documentation** - User guides and developer documentation

### Week 11-12: Testing and Deployment
1. **Comprehensive Testing** - Unit, integration, performance, and usability testing
2. **Security Hardening** - Access control, audit logging, and data validation
3. **Performance Tuning** - Database optimization, caching strategy, load balancing
4. **Deployment Preparation** - Migration scripts, backup procedures, rollback plans
5. **Training Materials** - Tutorials, video guides, and help documentation

## Risk Mitigation

### Technical Risks
1. **NLP Model Performance** - Mitigation: Start with rule-based extraction, gradually add NLP with fallback options
2. **Graph Visualization Performance** - Mitigation: Implement level-of-detail rendering, server-side graph processing
3. **Database Complexity** - Mitigation: Incremental schema changes, thorough testing, backup strategy
4. **Browser Compatibility** - Mitigation: Progressive enhancement, polyfills for older browsers

### Integration Risks
1. **Queue System Integration** - Mitigation: Well-defined API contracts, backward compatibility, phased rollout
2. **External Service Dependencies** - Mitigation: Circuit breakers, caching, fallback to local processing
3. **Data Consistency** - Mitigation: Transactional operations, conflict resolution, audit trails

### Business Risks
1. **User Adoption** - Mitigation: Intuitive UI, comprehensive training, gradual feature introduction
2. **Data Quality** - Mitigation: Validation rules, verification workflows, quality metrics
3. **System Performance** - Mitigation: Performance testing, monitoring, scalability planning

## Success Metrics
1. **Entity Extraction Accuracy** - Achieve 90%+ accuracy on test datasets
2. **Deduplication Precision** - 95%+ precision on duplicate detection
3. **Verification Completion Time** - Reduce average verification time by 50%
4. **Graph Visualization Performance** - Render 1000+ node graphs in under 2 seconds
5. **User Satisfaction** - 85%+ satisfaction score from admin users
6. **System Uptime** - 99.9% availability for entity management functions

## Post-Implementation Roadmap
1. **Phase 3.1** - Machine learning for relationship prediction and entity classification
2. **Phase 3.2** - Real-time collaboration features for entity review
3. **Phase 3.3** - Mobile-responsive entity management interface
4. **Phase 3.4** - Advanced analytics and predictive insights
5. **Phase 3.5** - API marketplace for third-party entity services

## Task Progress
- [x] Create Phase 3 implementation plan document
- [x] Review existing entity infrastructure and database schema
- [x] Design comprehensive entity management system architecture
- [x] Create detailed implementation plan with specific file changes
- [x] Define testing strategy and success metrics
- [x] Present plan to user for approval