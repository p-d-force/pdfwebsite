<?php
/**
 * Database status checker for PDFWEBSITE
 */

require_once __DIR__ . '/../admin/includes/config.php';
require_once __DIR__ . '/../admin/includes/Database.php';

echo "PDFWEBSITE Database Status Check\n";
echo "================================\n\n";

try {
    $db = Database::getInstance();
    $pdo = $db->getConnection();
    
    // Get all tables
    $stmt = $pdo->query("SHOW TABLES");
    $tables = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    echo "Found " . count($tables) . " tables:\n";
    foreach ($tables as $table) {
        echo "  - $table\n";
    }
    echo "\n";
    
    // Check for core tables
    $coreTables = ['districts', 'cases', 'case_events', 'documents', 'admin_users', 'admin_sessions'];
    $missingCore = [];
    foreach ($coreTables as $table) {
        if (!in_array($table, $tables)) {
            $missingCore[] = $table;
        }
    }
    
    if (!empty($missingCore)) {
        echo "WARNING: Missing core tables: " . implode(', ', $missingCore) . "\n";
    } else {
        echo "✓ All core tables present\n";
    }
    
    // Check for enhanced schema tables
    $enhancedTables = ['intake_queue_items', 'field_extractions', 'extracted_persons', 'extracted_organizations'];
    $foundEnhanced = array_intersect($enhancedTables, $tables);
    
    if (!empty($foundEnhanced)) {
        echo "\nEnhanced schema tables found (" . count($foundEnhanced) . "/" . count($enhancedTables) . "):\n";
        foreach ($foundEnhanced as $table) {
            echo "  - $table\n";
        }
    } else {
        echo "\nEnhanced schema NOT found in database.\n";
        echo "You need to run: mysql -u USER -p DATABASE < backend/enhanced_schema.sql\n";
    }
    
    // Check queue table structure if exists
    if (in_array('intake_queue_items', $tables)) {
        echo "\nQueue Table Structure:\n";
        $stmt = $pdo->query("DESCRIBE intake_queue_items");
        $columns = $stmt->fetchAll();
        foreach ($columns as $col) {
            echo "  {$col['Field']} ({$col['Type']}) " . ($col['Null'] == 'NO' ? 'NOT NULL' : 'NULL') . "\n";
        }
    }
    
    // Count rows in key tables
    echo "\nRow Counts:\n";
    $countTables = array_intersect(['districts', 'cases', 'documents', 'admin_users'], $tables);
    foreach ($countTables as $table) {
        $stmt = $pdo->query("SELECT COUNT(*) as cnt FROM $table");
        $count = $stmt->fetch()['cnt'];
        echo "  $table: $count rows\n";
    }
    
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
    exit(1);
}

echo "\nCheck completed.\n";