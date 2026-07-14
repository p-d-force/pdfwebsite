<?php declare(strict_types=1);
/**
 * Route definitions — URL patterns mapped to Controller::method.
 * District routes use DB slug resolution (slug → district_code).
 * All existing .htaccess URL patterns are registered here.
 */

use App\Controllers\{
    HomeController,
    DistrictController,
    CaseController,
    ArticleController,
    DataPortalController,
    SearchController,
    ApiController,
};

return [
    // ── Pages ──
    '/'                        => [HomeController::class, 'index'],
    '/districts'               => [DistrictController::class, 'list'],
    '/districts/{slug}'        => [DistrictController::class, 'show'],
    '/cases'                   => [CaseController::class, 'list'],
    '/cases/{slug}'            => [CaseController::class, 'show'],
    '/articles'                => [ArticleController::class, 'list'],
    '/articles/{slug}'         => [ArticleController::class, 'show'],
    '/data'                    => [DataPortalController::class, 'index'],
    '/compare'                 => [DataPortalController::class, 'compare'],
    '/search'                  => [SearchController::class, 'index'],
    '/appearances'             => [HomeController::class, 'appearances'],
    '/about'                   => [HomeController::class, 'about'],
    '/submit'                  => [HomeController::class, 'submit'],
    '/updates'                 => [HomeController::class, 'updates'],

    // ── API ──
    '/api/data'                => [ApiController::class, 'data'],
    '/api/cases'               => [ApiController::class, 'cases'],
    '/api/articles'            => [ApiController::class, 'articles'],
    '/api/search'              => [ApiController::class, 'search'],
    '/api/submit'              => [ApiController::class, 'submit'],
    '/api/subscribe'           => [ApiController::class, 'subscribe'],

    // ── Feeds ──
    '/rss'                     => [HomeController::class, 'rss'],
    '/sitemap.xml'             => [HomeController::class, 'sitemap'],
];
