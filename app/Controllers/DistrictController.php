<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;
use App\Core\Database;
use App\Models\District;
use App\Components\DistrictDashboard;
use App\Components\DistrictCard;

class DistrictController
{
    /** GET /districts — list all districts */
    public function list(array $params = []): void
    {
        $districts = District::all();
        View::render('district-list', [
            'page_title' => 'Massachusetts School Districts',
            'page_description' => 'Browse Massachusetts school districts tracked by Parent Data Force. View restraint data, enrollment, cases, and advocacy history.',
            'districts' => $districts,
        ]);
    }

    /** GET /districts/{slug} — district dashboard (DB-driven) */
    public function show(array $params): void
    {
        $slug = $params['slug'] ?? '';
        if (!$slug) {
            http_response_code(404);
            View::render('errors/404', ['page_title' => 'District Not Found']);
            return;
        }

        // Try slug first, then DESE code (legacy URL compatibility)
        $district = District::findBySlug($slug)
                 ?? District::findByCode(strtoupper($slug));

        if (!$district) {
            http_response_code(404);
            View::render('errors/404', ['page_title' => 'District Not Found']);
            return;
        }

        $dashboard = new DistrictDashboard($district);
        View::render('district', [
            'page_title' => $district['district_name'],
            'page_description' => $district['description'] ?? 'District profile for ' . $district['district_name'],
            'dashboard' => $dashboard,
        ]);
    }
}
