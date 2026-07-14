<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;
use App\Core\Database;

class DataPortalController
{
    /** GET /data — data portal (restraint browser, trends) */
    public function index(array $params = []): void
    {
        View::render('data-portal', [
            'page_title' => 'Data Portal',
            'page_description' => 'Explore Massachusetts school district data — restraint and seclusion, enrollment, discipline, and attendance.',
        ]);
    }

    /** GET /compare — interactive district comparison */
    public function compare(array $params = []): void
    {
        View::render('compare', [
            'page_title' => 'District Comparison',
            'page_description' => 'Compare Massachusetts school districts side by side on restraint data, enrollment, and more.',
        ]);
    }
}

