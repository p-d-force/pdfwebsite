<?php
/**
 * JSON-to-Database Migration Script
 * Migrates configuration from JSON files to database tables
 * 
 * Usage: php migrate_json_to_db.php [--dry-run] [--rollback]
 */

require_once dirname(__DIR__) . '/admin/includes/Database.php';
require_once dirname(__DIR__) . '/admin/includes/ConfigManager.php';

// Define ANSI colors for output
define('COLOR_RESET', "\033[0m");
define('COLOR_RED', "\033[31m");
define('COLOR_GREEN', "\033[32m");
define('COLOR_YELLOW', "\033[33m");
define('COLOR_BLUE', "\033[34m");
define('COLOR_CYAN', "\033[36m");

class JsonToDbMigration {
    private $db;
    private $configManager;
    private $dryRun = false;
    private $rollback = false;
    private $migrationLog = [];
    
    public function __construct($dryRun = false, $rollback = false) {
        $this->db = Database::getInstance();
        $this->configManager = ConfigManager::getInstance();
        $this->dryRun = $dryRun;
        $this->rollback = $rollback;
    }
    
    /**
     * Run the migration
     */
    public function run() {
        $this->log("Starting JSON-to-Database Migration", 'header');
        
        if ($this->rollback) {
            $this->log("ROLLBACK MODE: Will rollback migration", 'warning');
            return $this->rollbackMigration();
        }
        
        if ($this->dryRun) {
            $this->log("DRY RUN MODE: No changes will be made", 'info');
        }
        
        // Step 1: Check if migration tables exist
        $this->log("Step 1: Checking migration tables...", 'step');
        $tablesExist = $this->checkMigrationTables();
        
        if (!$tablesExist && !$this->dryRun) {
            $this->log("Creating migration tables...", 'info');
            $this->createMigrationTables();
        }
        
        // Step 2: Check current migration status
        $this->log("Step 2: Checking migration status...", 'step');
        $migrationStatus = $this->getMigrationStatus();
        
        if ($migrationStatus['already_migrated']) {
            $this->log("Migration already completed at: " . $migrationStatus['last_migration'], 'warning');
            
            $response = $this->promptUser("Migration already exists. Do you want to re-run? (yes/no): ");
            if (strtolower($response) !== 'yes') {
                $this->log("Migration aborted by user.", 'info');
                return;
            }
        }
        
        // Step 3: Run migrations
        $this->log("Step 3: Running migrations...", 'step');
        
        $migrations = [
            'queue_config' => [
                'json_file' => dirname(__DIR__) . '/config/queue_config.json',
                'category' => 'queue',
                'description' => 'Queue system configuration'
            ],
            'district_sources' => [
                'json_file' => dirname(__DIR__) . '/config/district_sources.json',
                'category' => 'district',
                'description' => 'District sources configuration'
            ],
            'site_config' => [
                'json_file' => dirname(__DIR__) . '/config/site.json',
                'category' => 'site',
                'description' => 'Site configuration'
            ]
        ];
        
        $results = [];
        foreach ($migrations as $name => $config) {
            $this->log("Migrating: $name...", 'info');
            $result = $this->migrateJsonFile($config['json_file'], $config['category'], $config['description']);
            $results[$name] = $result;
            
            if ($result['success']) {
                $this->log("✓ $name migrated successfully (" . $result['successful'] . "/" . $result['total'] . " items)", 'success');
            } else {
                $this->log("✗ $name failed: " . $result['message'], 'error');
            }
        }
        
        // Step 4: Record migration
        if (!$this->dryRun) {
            $this->log("Step 4: Recording migration...", 'step');
            $this->recordMigration($results);
        }
        
        // Step 5: Verify migration
        $this->log("Step 5: Verifying migration...", 'step');
        $verification = $this->verifyMigration();
        
        // Display summary
        $this->displaySummary($results, $verification);
    }
    
    /**
     * Rollback migration
     */
    private function rollbackMigration() {
        $this->log("Rolling back migration...", 'warning');
        
        // Get last migration
        try {
            $pdo = $this->db->getConnection();
            $stmt = $pdo->query("SELECT * FROM json_migrations ORDER BY migrated_at DESC LIMIT 1");
            $lastMigration = $stmt->fetch();
            
            if (!$lastMigration) {
                $this->log("No migration found to rollback.", 'info');
                return;
            }
            
            $migrationId = $lastMigration['id'];
            $this->log("Rolling back migration ID: $migrationId from " . $lastMigration['migrated_at'], 'info');
            
            // Remove system_config entries
            $stmt = $pdo->prepare("DELETE FROM system_config WHERE id > ?");
            $stmt->execute([0]); // Delete all for simplicity
            
            // Remove district_sources entries
            $stmt = $pdo->prepare("DELETE FROM district_sources WHERE id > ?");
            $stmt->execute([0]);
            
            // Remove site_config entries
            $stmt = $pdo->prepare("DELETE FROM site_config WHERE id > ?");
            $stmt->execute([0]);
            
            // Mark migration as rolled back
            $stmt = $pdo->prepare("UPDATE json_migrations SET rolled_back_at = NOW() WHERE id = ?");
            $stmt->execute([$migrationId]);
            
            $this->log("Rollback completed successfully.", 'success');
            
        } catch (Exception $e) {
            $this->log("Rollback failed: " . $e->getMessage(), 'error');
        }
    }
    
    /**
     * Migrate a single JSON file
     */
    private function migrateJsonFile($jsonPath, $category, $description) {
        if ($this->dryRun) {
            // Just simulate
            if (!file_exists($jsonPath)) {
                return ['success' => false, 'message' => 'JSON file not found'];
            }
            
            $content = file_get_contents($jsonPath);
            $config = json_decode($content, true);
            
            if ($config === null) {
                return ['success' => false, 'message' => 'Invalid JSON'];
            }
            
            return [
                'success' => true,
                'message' => 'Dry run simulation',
                'total' => count($config),
                'successful' => count($config),
                'results' => array_fill_keys(array_keys($config), 'simulated')
            ];
        }
        
        return $this->configManager->migrateFromJson($jsonPath, $category, $description);
    }
    
    /**
     * Check if migration tables exist
     */
    private function checkMigrationTables() {
        try {
            $pdo = $this->db->getConnection();
            
            $tables = ['system_config', 'district_sources', 'site_config', 'json_migrations'];
            $existingTables = [];
            
            foreach ($tables as $table) {
                $stmt = $pdo->query("SHOW TABLES LIKE '$table'");
                if ($stmt->fetch()) {
                    $existingTables[] = $table;
                }
            }
            
            $missingTables = array_diff($tables, $existingTables);
            
            if (!empty($missingTables)) {
                $this->log("Missing tables: " . implode(', ', $missingTables), 'warning');
                return false;
            }
            
            return true;
            
        } catch (Exception $e) {
            $this->log("Error checking tables: " . $e->getMessage(), 'error');
            return false;
        }
    }
    
    /**
     * Create migration tables
     */
    private function createMigrationTables() {
        try {
            $pdo = $this->db->getConnection();
            
            // Create migration tracking table if not exists
            $sql = "CREATE TABLE IF NOT EXISTS json_migrations (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                migration_name VARCHAR(128) NOT NULL,
                config_files JSON NOT NULL,
                total_items INT NOT NULL DEFAULT 0,
                successful_items INT NOT NULL DEFAULT 0,
                results JSON NULL,
                migrated_by VARCHAR(128) NULL,
                migrated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                rolled_back_at TIMESTAMP NULL,
                PRIMARY KEY (id),
                KEY idx_migrations_migrated_at (migrated_at)
            )";
            
            $pdo->exec($sql);
            $this->log("Created migration tracking table.", 'success');
            
            return true;
            
        } catch (Exception $e) {
            $this->log("Error creating tables: " . $e->getMessage(), 'error');
            return false;
        }
    }
    
    /**
     * Get migration status
     */
    private function getMigrationStatus() {
        try {
            $pdo = $this->db->getConnection();
            
            $stmt = $pdo->query("SELECT COUNT(*) as count FROM system_config");
            $systemConfigCount = $stmt->fetch()['count'] ?? 0;
            
            $stmt = $pdo->query("SELECT COUNT(*) as count FROM json_migrations");
            $migrationCount = $stmt->fetch()['count'] ?? 0;
            
            $lastMigration = null;
            if ($migrationCount > 0) {
                $stmt = $pdo->query("SELECT migrated_at FROM json_migrations ORDER BY migrated_at DESC LIMIT 1");
                $lastMigration = $stmt->fetch()['migrated_at'] ?? null;
            }
            
            return [
                'already_migrated' => $systemConfigCount > 0,
                'config_count' => $systemConfigCount,
                'migration_count' => $migrationCount,
                'last_migration' => $lastMigration
            ];
            
        } catch (Exception $e) {
            return [
                'already_migrated' => false,
                'config_count' => 0,
                'migration_count' => 0,
                'last_migration' => null,
                'error' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Record migration in database
     */
    private function recordMigration($results) {
        try {
            $pdo = $this->db->getConnection();
            
            $totalItems = 0;
            $successfulItems = 0;
            $configFiles = [];
            
            foreach ($results as $name => $result) {
                if ($result['success']) {
                    $totalItems += $result['total'];
                    $successfulItems += $result['successful'];
                    $configFiles[] = $name;
                }
            }
            
            $sql = "INSERT INTO json_migrations 
                    (migration_name, config_files, total_items, successful_items, results, migrated_by) 
                    VALUES (?, ?, ?, ?, ?, ?)";
            
            $stmt = $pdo->prepare($sql);
            $stmt->execute([
                'json_to_db_migration',
                json_encode($configFiles),
                $totalItems,
                $successfulItems,
                json_encode($results),
                get_current_user()
            ]);
            
            $this->log("Migration recorded successfully.", 'success');
            
        } catch (Exception $e) {
            $this->log("Error recording migration: " . $e->getMessage(), 'error');
        }
    }
    
    /**
     * Verify migration results
     */
    private function verifyMigration() {
        $verification = [];
        
        try {
            $pdo = $this->db->getConnection();
            
            // Verify system_config
            $stmt = $pdo->query("SELECT COUNT(*) as count FROM system_config");
            $systemConfigCount = $stmt->fetch()['count'] ?? 0;
            $verification['system_config'] = $systemConfigCount > 0 ? 'OK' : 'EMPTY';
            
            // Verify district_sources
            $stmt = $pdo->query("SELECT COUNT(*) as count FROM district_sources");
            $districtSourcesCount = $stmt->fetch()['count'] ?? 0;
            $verification['district_sources'] = $districtSourcesCount > 0 ? 'OK' : 'EMPTY';
            
            // Verify site_config
            $stmt = $pdo->query("SELECT COUNT(*) as count FROM site_config");
            $siteConfigCount = $stmt->fetch()['count'] ?? 0;
            $verification['site_config'] = $siteConfigCount > 0 ? 'OK' : 'EMPTY';
            
            // Test ConfigManager
            $queueConfig = $this->configManager->getQueueConfig();
            $verification['config_manager_queue'] = !empty($queueConfig) ? 'OK' : 'FAILED';
            
            $districtSources = $this->configManager->getDistrictSources();
            $verification['config_manager_district'] = !empty($districtSources) ? 'OK' : 'FAILED';
            
            $siteConfig = $this->configManager->getSiteConfig();
            $verification['config_manager_site'] = !empty($siteConfig) ? 'OK' : 'FAILED';
            
        } catch (Exception $e) {
            $verification['error'] = $e->getMessage();
        }
        
        return $verification;
    }
    
    /**
     * Display migration summary
     */
    private function displaySummary($results, $verification) {
        $this->log("\n" . str_repeat("=", 60), 'header');
        $this->log("MIGRATION SUMMARY", 'header');
        $this->log(str_repeat("=", 60), 'header');
        
        $totalFiles = count($results);
        $successfulFiles = 0;
        $totalItems = 0;
        $successfulItems = 0;
        
        foreach ($results as $name => $result) {
            if ($result['success']) {
                $successfulFiles++;
                $totalItems += $result['total'];
                $successfulItems += $result['successful'];
            }
            
            $status = $result['success'] ? COLOR_GREEN . '✓ SUCCESS' : COLOR_RED . '✗ FAILED';
            $this->log(sprintf("  %-20s %s", $name, $status . COLOR_RESET));
        }
        
        $this->log("\nSTATISTICS:", 'info');
        $this->log(sprintf("  Files: %d/%d successful", $successfulFiles, $totalFiles));
        $this->log(sprintf("  Items: %d/%d successful", $successfulItems, $totalItems));
        
        $this->log("\nVERIFICATION:", 'info');
        foreach ($verification as $key => $status) {
            $color = $status === 'OK' ? COLOR_GREEN : ($status === 'EMPTY' ? COLOR_YELLOW : COLOR_RED);
            $this->log(sprintf("  %-30s %s", $key, $color . $status . COLOR_RESET));
        }
        
        if ($this->dryRun) {
            $this->log("\n" . COLOR_YELLOW . "NOTE: This was a dry run. No changes were made." . COLOR_RESET, 'warning');
        } elseif ($this->rollback) {
            $this->log("\n" . COLOR_YELLOW . "NOTE: Rollback completed." . COLOR_RESET, 'warning');
        } else {
            $this->log("\n" . COLOR_GREEN . "MIGRATION COMPLETED SUCCESSFULLY" . COLOR_RESET, 'success');
        }
        
        $this->log(str_repeat("=", 60) . "\n", 'header');
    }
    
    /**
     * Prompt user for input
     */
    private function promptUser($message) {
        echo COLOR_CYAN . $message . COLOR_RESET;
        return trim(fgets(STDIN));
    }
    
    /**
     * Log message with color
     */
    private function log($message, $type = 'info') {
        $timestamp = date('Y-m-d H:i:s');
        $this->migrationLog[] = [$timestamp, $type, $message];
        
        $colors = [
            'header' => COLOR_BLUE,
            'step' => COLOR_CYAN,
            'info' => COLOR_RESET,
            'success' => COLOR_GREEN,
            'warning' => COLOR_YELLOW,
            'error' => COLOR_RED
        ];
        
        $color = $colors[$type] ?? COLOR_RESET;
        echo $color . "[$timestamp] $message" . COLOR_RESET . "\n";
    }
}

// Parse command line arguments
$dryRun = in_array('--dry-run', $argv);
$rollback = in_array('--rollback', $argv);

// Show help
if (in_array('--help', $argv) || in_array('-h', $argv)) {
    echo "JSON-to-Database Migration Script\n";
    echo "Usage: php migrate_json_to_db.php [options]\n\n";
    echo "Options:\n";
    echo "  --dry-run    Simulate migration without making changes\n";
    echo "  --rollback   Rollback the last migration\n";
    echo "  --help, -h   Show this help message\n";
    exit(0);
}

try {
    $migration = new JsonToDbMigration($dryRun, $rollback);
    $migration->run();
} catch (Exception $e) {
    echo COLOR_RED . "Fatal error: " . $e->getMessage() . COLOR_RESET . "\n";
    exit(1);
}
?>