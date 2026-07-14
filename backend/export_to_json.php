#!/usr/bin/env php
<?php
/**
 * Export MariaDB data to JSON files for public website
 * 
 * Usage: php export_to_json.php [--output-dir=/path] [--format=legacy|public]
 */

require_once __DIR__ . '/../admin/includes/config.php';
require_once __DIR__ . '/../admin/includes/Database.php';

$options = getopt('', ['output-dir:', 'format:', 'help', 'verbose']);

if (isset($options['help'])) {
    echo "Export MariaDB data to JSON files\n";
    echo "Usage: php export_to_json.php [options]\n";
    echo "Options:\n";
    echo "  --output-dir=PATH   Output directory (default: ../public_export)\n";
    echo "  --format=FORMAT     Output format: legacy (original structure) or public (simplified) (default: legacy)\n";
    echo "  --verbose           Show progress messages\n";
    echo "  --help              Show this help\n";
    exit(0);
}

$outputDir = $options['output-dir'] ?? dirname(__DIR__) . '/public_export';
$format = $options['format'] ?? 'legacy';
$verbose = isset($options['verbose']);

// Create output directory
if (!is_dir($outputDir)) {
    mkdir($outputDir, 0755, true);
    if ($verbose) echo "Created output directory: $outputDir\n";
}

$db = Database::getInstance();
$pdo = $db->getConnection();

try {
    if ($format === 'legacy') {
        exportLegacyFormat($pdo, $outputDir, $verbose);
    } else {
        exportPublicFormat($pdo, $outputDir, $verbose);
    }
    
    echo "Export completed successfully to $outputDir\n";
} catch (Exception $e) {
    echo "Export failed: " . $e->getMessage() . "\n";
    exit(1);
}

function exportLegacyFormat($pdo, $outputDir, $verbose) {
    // Export districts
    $stmt = $pdo->query("SELECT * FROM districts ORDER BY district_code");
    $districts = $stmt->fetchAll();
    
    foreach ($districts as $district) {
        $districtCode = $district['district_code'];
        $districtDir = $outputDir . '/cases/' . $districtCode;
        
        if (!is_dir($districtDir)) {
            mkdir($districtDir, 0755, true);
        }
        
        // Get cases for this district
        $caseStmt = $pdo->prepare("
            SELECT c.* 
            FROM cases c 
            WHERE c.district_id = ? 
            ORDER BY c.case_code
        ");
        $caseStmt->execute([$district['id']]);
        $cases = $caseStmt->fetchAll();
        
        $caseCodes = [];
        foreach ($cases as $case) {
            $caseCodes[] = $case['case_code'];
            
            // Export case metadata
            exportCaseMetadata($pdo, $case, $district, $districtDir, $verbose);
        }
        
        // Create district metadata
        $districtMetadata = [
            'district' => $district['district_code'],
            'districtName' => $district['district_name'],
            'location' => $district['location'],
            'status' => $district['status'],
            'cases' => $caseCodes,
            'notes' => $district['notes'],
            'relatedDistricts' => [] // Would need separate table
        ];
        
        $districtFile = $districtDir . '/metadata.json';
        file_put_contents($districtFile, json_encode($districtMetadata, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
        
        if ($verbose) echo "Exported district: $districtCode\n";
    }
}

function exportCaseMetadata($pdo, $case, $district, $districtDir, $verbose) {
    $caseCode = $case['case_code'];
    $caseDir = $districtDir . '/' . $caseCode;
    
    if (!is_dir($caseDir)) {
        mkdir($caseDir, 0755, true);
        mkdir($caseDir . '/original-request', 0755, true);
        mkdir($caseDir . '/responses', 0755, true);
        mkdir($caseDir . '/appeals', 0755, true);
        mkdir($caseDir . '/recordings', 0755, true);
    }
    
    // Get events for this case
    $eventStmt = $pdo->prepare("
        SELECT * FROM case_events 
        WHERE case_id = ? 
        ORDER BY event_date, sort_order
    ");
    $eventStmt->execute([$case['id']]);
    $events = $eventStmt->fetchAll();
    
    // Convert events to timeline entries
    $timeline = [];
    foreach ($events as $event) {
        $entry = [
            'entryId' => $event['id'],
            'date' => $event['event_date'],
            'type' => $event['event_type'],
            'title' => $event['title'],
            'description' => $event['description'],
            'status' => $event['status'],
            'documents' => [], // Would need to fetch documents for this event
            'deadline' => null, // Events don't have deadline field
            'deadlineStatus' => null
        ];
        
        // Get documents for this event
        $docStmt = $pdo->prepare("
            SELECT relative_path FROM documents 
            WHERE case_event_id = ? 
            ORDER BY document_date
        ");
        $docStmt->execute([$event['id']]);
        $documents = $docStmt->fetchAll(PDO::FETCH_COLUMN);
        
        if ($documents) {
            // Convert relative paths to case-relative paths
            foreach ($documents as $docPath) {
                $entry['documents'][] = 'cases/' . $district['district_code'] . '/' . $caseCode . '/' . $docPath;
            }
        }
        
        $timeline[] = $entry;
    }
    
    // Get documents for this case (not associated with events)
    $docStmt = $pdo->prepare("
        SELECT * FROM documents 
        WHERE case_id = ? AND case_event_id IS NULL 
        ORDER BY document_date
    ");
    $docStmt->execute([$case['id']]);
    $documents = $docStmt->fetchAll();
    
    // Build requested items from subject/description? Not in schema
    $requestedItems = [];
    if (!empty($case['subject'])) {
        $requestedItems = [$case['subject']];
    }
    
    // Build case metadata
    $caseMetadata = [
        'caseId' => $case['case_code'],
        'prrNumber' => $case['case_code'],
        'district' => $district['district_code'],
        'districtName' => $district['district_name'],
        'districtCode' => $district['district_code'],
        'location' => $district['location'],
        'type' => $case['case_type'],
        'status' => $case['status'],
        'statusLabel' => $case['status'], // Same as status
        'statusReason' => $case['stage'],
        'priority' => 'medium', // Not in schema
        'filedDate' => $case['filed_date'],
        'statutoryDeadline' => $case['next_deadline'],
        'appealDeadline' => null, // Not in schema
        'currentStage' => $case['stage'],
        'subject' => $case['subject'],
        'requester' => 'Unknown', // Not in schema
        'relatedCases' => [], // Would need case_links table
        'relatedDistricts' => [],
        'recurrenceNotes' => $case['recurrence_notes'],
        'caseType' => strtolower($case['case_type']),
        'requestedItems' => $requestedItems,
        'timeline' => $timeline
    ];
    
    $caseFile = $caseDir . '/metadata.json';
    file_put_contents($caseFile, json_encode($caseMetadata, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    
    if ($verbose) echo "  Exported case: $caseCode\n";
}

function exportPublicFormat($pdo, $outputDir, $verbose) {
    // Simplified public format - all data in single files
    $output = [];
    
    // Export districts
    $stmt = $pdo->query("SELECT district_code, district_name, location, status, notes FROM districts");
    $output['districts'] = $stmt->fetchAll();
    
    // Export cases with minimal info
    $stmt = $pdo->query("
        SELECT c.case_code, c.title, c.case_type, c.status, c.stage, c.subject,
               c.filed_date, c.next_deadline, c.next_deadline_description,
               d.district_code, d.district_name
        FROM cases c 
        JOIN districts d ON c.district_id = d.id
        ORDER BY c.next_deadline ASC
    ");
    $output['cases'] = $stmt->fetchAll();
    
    // Export events
    $stmt = $pdo->query("
        SELECT e.event_date, e.event_type, e.title, e.description, e.status,
               c.case_code
        FROM case_events e
        JOIN cases c ON e.case_id = c.id
        ORDER BY e.event_date DESC
        LIMIT 1000
    ");
    $output['recent_events'] = $stmt->fetchAll();
    
    $publicFile = $outputDir . '/public_data.json';
    file_put_contents($publicFile, json_encode($output, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    
    if ($verbose) echo "Exported public format to $publicFile\n";
}